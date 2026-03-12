from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Payment
from .serializers import PaymentSerializer
import uuid
import requests

ORDER_SERVICE_URL = "http://order-service:8000"

class PaymentListCreate(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'credit_card')
        customer_id = request.data.get('customer_id')
        
        if not order_id or not amount:
            return Response(
                {"error": "order_id and amount are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment record
        payment = Payment(
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            status='pending',
            reference_number=str(uuid.uuid4())
        )
        
        # Process payment
        try:
            if payment.process_payment():
                # Update order status to confirmed
                try:
                    requests.put(
                        f"{ORDER_SERVICE_URL}/orders/{order_id}/status/",
                        json={'status': 'confirmed'},
                        timeout=5
                    )
                except:
                    pass  # Order update is non-critical
                
                serializer = self.get_serializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                payment.status = 'failed'
                payment.save()
                return Response(
                    {"error": "Payment processing failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            payment.status = 'failed'
            payment.save()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class PaymentProcess(APIView):
    """Process pending payment"""
    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if payment.status == 'completed':
                return Response(
                    {"error": "Payment already completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if payment.process_payment():
                serializer = PaymentSerializer(payment)
                return Response(serializer.data)
            else:
                return Response(
                    {"error": "Payment processing failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentRefund(APIView):
    """Refund a payment"""
    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            refund_amount = request.data.get('amount')
            reason = request.data.get('reason', '')
            
            if payment.refund(refund_amount, reason):
                serializer = PaymentSerializer(payment)
                return Response(serializer.data)
            else:
                return Response(
                    {"error": "Refund failed - insufficient balance or invalid payment status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderPayment(APIView):
    def get(self, request, order_id):
        payments = Payment.objects.filter(order_id=order_id).order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentStatistics(APIView):
    """Get payment statistics"""
    def get(self, request):
        total_payments = Payment.objects.filter(status='completed').count()
        total_amount = sum(p.amount for p in Payment.objects.filter(status='completed'))
        pending_amount = sum(p.amount for p in Payment.objects.filter(status='pending'))
        
        return Response({
            'total_payments': total_payments,
            'total_amount': float(total_amount),
            'pending_amount': float(pending_amount),
            'payment_methods': {
                'credit_card': Payment.objects.filter(payment_method='credit_card').count(),
                'bank_transfer': Payment.objects.filter(payment_method='bank_transfer').count(),
                'cash_on_delivery': Payment.objects.filter(payment_method='cash_on_delivery').count(),
            }
        })


class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Payment service healthy"}, status=status.HTTP_200_OK)

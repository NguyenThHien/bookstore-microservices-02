from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from .models import Shipment, TrackingUpdate
from .serializers import ShipmentSerializer, TrackingUpdateSerializer
import uuid


class ShipmentListCreate(generics.ListCreateAPIView):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        customer_id = request.data.get('customer_id')
        address = request.data.get('address')
        city = request.data.get('city', '')
        zip_code = request.data.get('zip_code', '')
        country = request.data.get('country', '')
        carrier = request.data.get('carrier', 'standard')
        recipient_name = request.data.get('recipient_name', '')
        recipient_phone = request.data.get('recipient_phone', '')
        
        if not order_id or not address:
            return Response(
                {"error": "order_id and address are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique tracking number
        tracking_number = f"VN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        
        # Estimate delivery date (5-7 business days)
        estimated_delivery = timezone.now() + timedelta(days=7)
        
        shipment = Shipment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            tracking_number=tracking_number,
            address=address,
            city=city,
            zip_code=zip_code,
            country=country,
            carrier=carrier,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            estimated_delivery_date=estimated_delivery.date(),
            status='pending'
        )
        
        # Create initial tracking update
        TrackingUpdate.objects.create(
            shipment=shipment,
            status='pending',
            location='Order received, preparing for shipment',
            description='Your order has been received and is being prepared'
        )
        
        serializer = self.get_serializer(shipment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShipmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer


class ShipmentUpdateStatus(APIView):
    """Update shipment status"""
    def put(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
            new_status = request.data.get('status')
            location = request.data.get('location', '')
            description = request.data.get('description', '')
            
            if new_status not in dict(Shipment.STATUS_CHOICES):
                return Response(
                    {"error": "Invalid status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            shipment.status = new_status
            shipment.last_location = location
            
            if new_status == 'shipped':
                shipment.shipped_at = timezone.now()
            elif new_status == 'delivered':
                shipment.delivered_at = timezone.now()
            
            shipment.save()
            
            # Create tracking update
            TrackingUpdate.objects.create(
                shipment=shipment,
                status=new_status,
                location=location,
                description=description
            )
            
            serializer = ShipmentSerializer(shipment)
            return Response(serializer.data)
        except Shipment.DoesNotExist:
            return Response(
                {"error": "Shipment not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ShipmentTrackingHistory(APIView):
    """Get complete tracking history for a shipment"""
    def get(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
            tracking_updates = TrackingUpdate.objects.filter(shipment=shipment)
            serializer = TrackingUpdateSerializer(tracking_updates, many=True)
            
            return Response({
                'shipment': ShipmentSerializer(shipment).data,
                'history': serializer.data
            })
        except Shipment.DoesNotExist:
            return Response(
                {"error": "Shipment not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class TrackingNumberLookup(APIView):
    """Lookup shipment by tracking number"""
    def get(self, request):
        tracking_number = request.query_params.get('tracking_number')
        
        if not tracking_number:
            return Response(
                {"error": "tracking_number parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
            tracking_updates = TrackingUpdate.objects.filter(shipment=shipment)
            
            return Response({
                'shipment': ShipmentSerializer(shipment).data,
                'history': TrackingUpdateSerializer(tracking_updates, many=True).data
            })
        except Shipment.DoesNotExist:
            return Response(
                {"error": "Tracking number not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderShipment(APIView):
    """Get shipment for an order"""
    def get(self, request, order_id):
        shipments = Shipment.objects.filter(order_id=order_id).order_by('-created_at')
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


class ShipmentStatistics(APIView):
    """Get shipment statistics"""
    def get(self, request):
        total_shipments = Shipment.objects.count()
        delivered = Shipment.objects.filter(status='delivered').count()
        in_transit = Shipment.objects.filter(status='in_transit').count()
        failed = Shipment.objects.filter(status='failed').count()
        
        return Response({
            'total_shipments': total_shipments,
            'delivered': delivered,
            'in_transit': in_transit,
            'failed': failed,
            'delivery_status': {
                'pending': Shipment.objects.filter(status='pending').count(),
                'confirmed': Shipment.objects.filter(status='confirmed').count(),
                'processing': Shipment.objects.filter(status='processing').count(),
                'shipped': Shipment.objects.filter(status='shipped').count(),
                'out_for_delivery': Shipment.objects.filter(status='out_for_delivery').count(),
            }
        })


class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Shipping service healthy"}, status=status.HTTP_200_OK)

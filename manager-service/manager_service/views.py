from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Report
from .serializers import ReportSerializer

class ReportList(generics.ListCreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

class ReportDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Manager service healthy"}, status=status.HTTP_200_OK)

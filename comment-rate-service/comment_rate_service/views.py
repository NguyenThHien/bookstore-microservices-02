from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from .models import Rating
from .serializers import RatingSerializer

class RatingListCreate(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

class RatingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

class BookRatings(APIView):
    def get(self, request, book_id):
        ratings = Rating.objects.filter(book_id=book_id)
        serializer = RatingSerializer(ratings, many=True)
        avg_rating = ratings.aggregate(avg=models.Avg('rating'))['avg'] or 0
        return Response({'ratings': serializer.data, 'average': avg_rating})

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Comment-Rate service healthy"}, status=status.HTTP_200_OK)

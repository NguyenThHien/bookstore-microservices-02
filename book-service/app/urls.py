from django.urls import path
from .views import BookListCreate, BookDetail, BookSearch, HealthCheck

urlpatterns = [
    path('', HealthCheck.as_view()),
    path('books/', BookListCreate.as_view()),
    path('books/<int:pk>/', BookDetail.as_view()),
    path('books/search/', BookSearch.as_view()),
]
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ratings/', views.RatingListCreate.as_view()),
    path('ratings/<int:pk>/', views.RatingDetail.as_view()),
    path('books/<int:book_id>/ratings/', views.BookRatings.as_view()),
    path('health/', views.HealthCheck.as_view()),
]

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('categories/', views.CategoryList.as_view()),
    path('categories/<int:pk>/', views.CategoryDetail.as_view()),
    path('subcategories/', views.SubcategoryList.as_view()),
    path('subcategories/<int:pk>/', views.SubcategoryDetail.as_view()),
    path('health/', views.HealthCheck.as_view()),
]

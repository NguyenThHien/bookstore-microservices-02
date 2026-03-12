from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('staff/', views.StaffListCreate.as_view(), name='staff-list'),
    path('staff/<int:pk>/', views.StaffDetail.as_view(), name='staff-detail'),
    path('staff/role/<str:role>/', views.StaffByRole.as_view(), name='staff-by-role'),
    path('staff/<int:staff_id>/permissions/', views.StaffPermissions.as_view(), name='staff-permissions'),
    path('activities/', views.StaffActivityLog.as_view(), name='activity-log'),
    path('activities/staff/<int:staff_id>/', views.StaffActivityLog.as_view(), name='staff-activity-log'),
    path('activities/record/', views.RecordActivity.as_view(), name='record-activity'),
    path('shifts/', views.ShiftManagement.as_view(), name='shifts-list'),
    path('shifts/staff/<int:staff_id>/', views.ShiftManagement.as_view(), name='staff-shifts'),
    path('shifts/<int:shift_id>/', views.ShiftDetail.as_view(), name='shift-detail'),
    path('health/', views.HealthCheck.as_view(), name='health'),
]

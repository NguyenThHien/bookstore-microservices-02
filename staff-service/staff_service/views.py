from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .models import Staff, StaffActivity, Shift
from .serializers import StaffSerializer, StaffActivitySerializer, ShiftSerializer

class StaffListCreate(generics.ListCreateAPIView):
    queryset = Staff.objects.filter(is_active=True)
    serializer_class = StaffSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        email = self.request.query_params.get("email")
        if email:
            qs = qs.filter(email__iexact=email.strip())
        return qs

class StaffDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class StaffByRole(APIView):
    """Get staff by role"""
    def get(self, request, role):
        if role not in ['admin', 'manager', 'operator', 'accountant', 'inventory']:
            return Response(
                {"error": "Invalid role"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        staff = Staff.objects.filter(role=role, is_active=True)
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)

class StaffPermissions(APIView):
    """Get staff permissions"""
    def get(self, request, staff_id):
        try:
            staff = Staff.objects.get(id=staff_id)
            return Response({
                'staff_id': staff.id,
                'staff_name': staff.name,
                'role': staff.role,
                'permissions': staff.permissions
            })
        except Staff.DoesNotExist:
            return Response(
                {"error": "Staff not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, staff_id):
        """Update staff permissions"""
        try:
            staff = Staff.objects.get(id=staff_id)
            permissions = request.data.get('permissions', [])
            
            # Validate permissions
            valid_permissions = [p[0] for p in Staff.PERMISSION_CHOICES]
            for perm in permissions:
                if perm not in valid_permissions:
                    return Response(
                        {"error": f"Invalid permission: {perm}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            staff.permissions = permissions
            staff.save()
            
            # Log activity
            StaffActivity.objects.create(
                staff=staff,
                action='update',
                resource_type='Staff',
                resource_id=staff.id,
                description=f"Permissions updated: {', '.join(permissions)}"
            )
            
            return Response({
                'message': 'Permissions updated',
                'permissions': staff.permissions
            })
        except Staff.DoesNotExist:
            return Response(
                {"error": "Staff not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class StaffActivityLog(APIView):
    """Get staff activity log"""
    def get(self, request, staff_id=None):
        activities = StaffActivity.objects.all()
        
        if staff_id:
            activities = activities.filter(staff_id=staff_id)
        
        # Filter by action
        action = request.query_params.get('action')
        if action:
            activities = activities.filter(action=action)
        
        # Filter by resource type
        resource_type = request.query_params.get('resource_type')
        if resource_type:
            activities = activities.filter(resource_type=resource_type)
        
        # Pagination
        limit = request.query_params.get('limit', 50)
        activities = activities[:int(limit)]
        
        serializer = StaffActivitySerializer(activities, many=True)
        return Response(serializer.data)

class RecordActivity(APIView):
    """Record a staff activity"""
    def post(self, request):
        staff_id = request.data.get('staff_id')
        action = request.data.get('action')
        resource_type = request.data.get('resource_type')
        resource_id = request.data.get('resource_id')
        description = request.data.get('description', '')
        
        if not staff_id or not action or not resource_type:
            return Response(
                {"error": "staff_id, action, and resource_type are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            staff = Staff.objects.get(id=staff_id)
            activity = StaffActivity.objects.create(
                staff=staff,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description
            )
            
            serializer = StaffActivitySerializer(activity)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Staff.DoesNotExist:
            return Response(
                {"error": "Staff not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ShiftManagement(APIView):
    """Manage staff shifts"""
    def get(self, request, staff_id=None):
        """Get shifts"""
        shifts = Shift.objects.all()
        
        if staff_id:
            shifts = shifts.filter(staff_id=staff_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            shifts = shifts.filter(status=status_filter)
        
        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create shift"""
        staff_id = request.data.get('staff_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        notes = request.data.get('notes', '')
        
        if not staff_id or not start_time or not end_time:
            return Response(
                {"error": "staff_id, start_time, and end_time are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            staff = Staff.objects.get(id=staff_id)
            shift = Shift.objects.create(
                staff=staff,
                start_time=start_time,
                end_time=end_time,
                notes=notes
            )
            
            serializer = ShiftSerializer(shift)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Staff.DoesNotExist:
            return Response(
                {"error": "Staff not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ShiftDetail(APIView):
    """Get/Update shift details"""
    def get(self, request, shift_id):
        try:
            shift = Shift.objects.get(id=shift_id)
            serializer = ShiftSerializer(shift)
            return Response(serializer.data)
        except Shift.DoesNotExist:
            return Response(
                {"error": "Shift not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, shift_id):
        try:
            shift = Shift.objects.get(id=shift_id)
            status_update = request.data.get('status')
            
            if status_update in ['scheduled', 'active', 'completed', 'cancelled']:
                shift.status = status_update
                shift.save()
            
            serializer = ShiftSerializer(shift)
            return Response(serializer.data)
        except Shift.DoesNotExist:
            return Response(
                {"error": "Shift not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Staff service healthy"}, status=status.HTTP_200_OK)

# app1/serializers.py
from rest_framework import serializers
from .models import Checklist, ChecklistItem, Complaint, Review, UserGroup, Users, Department, Location, Voucher

# ----- NEW -----
class DepartmentSerializer(serializers.ModelSerializer):
    total_users = serializers.IntegerField(read_only=True) 
    class Meta:
        model = Department
        fields = '__all__'

# (kept) – you already had this; leaving intact
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

# ----- UPDATED -----
class UsersSerializer(serializers.ModelSerializer):
    # write with department_id, read with department_name (and optional embedded object)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department",
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Users
        fields ='__all__'

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields ='__all__'

class ComplaintSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Complaint
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'
from .models import Building, Floor, LocationFamily, LocationType, Location

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'

class LocationFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationFamily
        fields = '__all__'

class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = '__all__'

from .models import RequestType, RequestFamily, WorkFamily, Workflow

class RequestFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestFamily
        fields ='__all__'

class WorkFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFamily
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = '__all__'

class RequestTypeSerializer(serializers.ModelSerializer):
    request_family = RequestFamilySerializer(read_only=True)
    work_family = WorkFamilySerializer(read_only=True)
    workflow = WorkflowSerializer(read_only=True)
    request_family_id = serializers.PrimaryKeyRelatedField(
        queryset=RequestFamily.objects.all(), source='request_family', write_only=True, required=False
    )
    work_family_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkFamily.objects.all(), source='work_family', write_only=True, required=False
    )
    workflow_id = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all(), source='workflow', write_only=True, required=False
    )

    class Meta:
        model = RequestType
        fields = '__all__'
class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = Checklist
        fields ='__all__'
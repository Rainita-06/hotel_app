from django.contrib import admin
from .models import (
    Department, UserGroup, Users, UserProfile, UserGroupMembership,
    Building, Floor, LocationFamily, LocationType, Location,
    RequestFamily, WorkFamily, Workflow, WorkflowStep, WorkflowTransition,
    Checklist, ChecklistItem, RequestType, ServiceRequest,
    ServiceRequestStep, ServiceRequestChecklist,
    Guest, GuestComment,
    Voucher, Review, Complaint,
    GymMember, GymVisitor, GymVisit
)
from django.contrib import admin
from .models import Voucher, RedemptionLog


class VoucherAdmin(admin.ModelAdmin):
    list_display = ("voucher_code", "guest_name", "room_no", "created_at", "redeemed", "redeemed_at")
    search_fields = ("voucher_code", "guest_name", "room_no")

@admin.register(RedemptionLog)
class RedemptionLogAdmin(admin.ModelAdmin):
    list_display = ("voucher", "scanned_at", "scanned_by", "success", "scanner_ip")
    list_filter = ("success",)

# Simple registrations
admin.site.register(Department)
admin.site.register(UserGroup)
admin.site.register(Users)
admin.site.register(UserProfile)
admin.site.register(UserGroupMembership)

admin.site.register(Building)
admin.site.register(Floor)
admin.site.register(LocationFamily)
admin.site.register(LocationType)
admin.site.register(Location)

admin.site.register(RequestFamily)
admin.site.register(WorkFamily)
admin.site.register(Workflow)
admin.site.register(WorkflowStep)
admin.site.register(WorkflowTransition)

admin.site.register(Checklist)
admin.site.register(ChecklistItem)
admin.site.register(RequestType)

admin.site.register(ServiceRequest)
admin.site.register(ServiceRequestStep)
admin.site.register(ServiceRequestChecklist)

admin.site.register(Guest)
admin.site.register(GuestComment)

admin.site.register(Voucher)
admin.site.register(Review)
admin.site.register(Complaint)

admin.site.register(GymMember)
admin.site.register(GymVisitor)
admin.site.register(GymVisit)

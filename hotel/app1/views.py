import os
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import group_required

# ---------- Auth ----------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return redirect("hotel_dashboard")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

# ---------- Modules ----------
@login_required
@group_required("AdminAccess")   # Only Admin group
def master_user(request):
    return render(request, "master_user.html")

@login_required
@group_required("AdminAccess")   # Only Admin group
def master_location(request):
    return render(request, "master_location.html")

@login_required
def hotel_dashboard(request):
    return render(request, "hotel_dashboard.html")

@login_required
def breakfast_voucher(request):
    return render(request, "breakfast_voucher.html")
# app1/views.py
import qrcode
import io
import base64
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Voucher

@login_required
def hotel_dashboard(request):
    qr_image = None
    voucher = None
    if request.method == "POST":
        room_no = request.POST.get("room_no")
        guest_name = request.POST.get("guest_name")
        date = request.POST.get("date")
        adults = int(request.POST.get("adults", 1))
        kids = int(request.POST.get("kids", 0))

        # Create or update voucher
        voucher, created = Voucher.objects.update_or_create(
            room_no=room_no,
            guest_name=guest_name,
            status="Active",
            defaults={
                "adults": adults,
                "kids": kids,
                "qty": adults + kids,
                "created_at": timezone.now(),
            }
        )

        # Generate QR with details
        qr_url = f"http://127.0.0.1:8000/room/{voucher.voucher_id}"
        qr_content = f"VoucherID:{voucher.voucher_id} | Room:{room_no} | Name:{customer_name} | Adults:{adults} | Kids:{kids} | Link:{qr_url}"
        qr = qrcode.make(qr_content)

        # Save to memory
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        # Save to MEDIA folder as file
        filename = f"voucher_{voucher.voucher_id}.png"
        file_path = os.path.join(settings.MEDIA_ROOT, "qrcodes", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())

        # Save file URL in DB
        voucher.qr_code = qr_url
        voucher.qr_code_image = f"/media/qrcodes/{filename}"
        voucher.save(update_fields=["qr_code", "qr_code_image"])

    return render(request, "dashboard.html", {"qr_image": qr_image, "voucher": voucher})

# app1/views.py (add this)
from django.http import HttpResponse

from django.http import HttpResponse
@login_required
def room_detail(request, voucher_id):
    voucher = get_object_or_404(Voucher, pk=voucher_id)

    # Auto-expire after first scan
    if voucher.status == "Active":
        voucher.status = "Checked"   # instead of "Checked"
        voucher.save(update_fields=["status"])
        message = "✅ This voucher has been used and is now expired."
    else:
        message = "⚠️ This voucher has already expired."

    return render(request, "room_detail.html", {"voucher": voucher, "message": message})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Department
from django.contrib import messages

def department_list(request):
    departments = Department.objects.all()
    return render(request, "departments.html", {"departments": departments})

def add_department(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get('description', '') 
        if name:
            Department.objects.create(name=name, description=description)
        messages.success(request,f"Department {name} added successfully!")
        return redirect("department_list")

def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get('description', '')
        if name:
            department.name = name
            department.description = description
            department.save()
        messages.success(request,f"Department {department.name} updated successfully!")
        return redirect("department_list")
    # ❌ Remove the render line (no separate template)
    return redirect("department_list")


def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    department_name = department.name
    department.delete()
    messages.success(request,f"Department {department_name} deleted successfully!")
    return redirect("department_list")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint, Users  # import Users

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Complaint


# ---------- Complaint List ----------
@login_required
def complaint_list(request):
    status_filter = request.GET.get("status", "Pending")

    # Check if the user is admin/staff
    is_admin = request.user.is_staff or request.user.is_superuser

    # Complaints queryset
    if is_admin:
        complaints = Complaint.objects.all()
        users = User.objects.all()  # Admin can see all users
    else:
        complaints = Complaint.objects.filter(user=request.user)
        users = [request.user]  # Normal users see only themselves

    # Apply status filter
    if status_filter == "All":
        complaints = complaints
    elif status_filter == "Closed":
        complaints = complaints.filter(status="CLOSED")
    elif status_filter == "On Hold":
        complaints = complaints.filter(status="ON_HOLD")
    else:  # Pending = NEW or ACCEPTED
        complaints = complaints.exclude(status="CLOSED")

    return render(request, "complaints.html", {
        "complaints": complaints,
        "users": users,
        "status_filter": status_filter,
        "is_admin": is_admin
    })


# ---------- Add Complaint ----------
@login_required
def add_complaint(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")

        try:
            if request.user.is_staff or request.user.is_superuser:
                custom_user = User.objects.get(id=user_id)  # Admin can assign to anyone
            else:
                # Force normal user to themselves (ignore dropdown tampering)
                custom_user = request.user
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("complaint_list")

        location = request.POST.get("location")
        title = request.POST.get("title")
        description = request.POST.get("description")

        Complaint.objects.create(
            user=custom_user,
            location=location,
            title=title,
            description=description,
            status="NEW"
        )

        messages.success(request, "Complaint added successfully.")
    return redirect("complaint_list")


# ---------- Update Complaint Status (Admin only) ----------
@login_required
def update_complaint_status(request, complaint_id, action):
    is_admin = request.user.is_staff or request.user.is_superuser
    if not is_admin:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect("complaint_list")

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if action == "accept":
        complaint.status = "ACCEPTED"
        complaint.owner = request.user.username
    elif action == "assign":
        complaint.status = "ON_HOLD"
    elif action == "close":
        complaint.status = "CLOSED"
        complaint.due_date = timezone.now()

    complaint.save()
    messages.success(request, "Complaint updated successfully.")
    return redirect("complaint_list")








@login_required
def edit_complaint(request, complaint_id):
    try:
        custom_user = Users.objects.get(full_name=request.user.username)
    except Users.DoesNotExist:
        return redirect("complaint_list")

    complaint = get_object_or_404(Complaint, id=complaint_id, user=custom_user)
    if request.method == "POST":
        complaint.category = request.POST.get("category")
        complaint.description = request.POST.get("description")
        complaint.status = request.POST.get("status")
        complaint.save()
        messages.success(request, "Complaint edited successfully.")
        return redirect("complaint_list")
    return redirect("complaint_list")


@login_required
def delete_complaint(request, complaint_id):
    try:
        custom_user = Users.objects.get(full_name=request.user.username)
    except Users.DoesNotExist:
        return redirect("complaint_list")

    complaint = get_object_or_404(Complaint, id=complaint_id, user=custom_user)
    complaint.delete()
    messages.success(request, "Complaint deleted successfully.")
    return redirect("complaint_list")


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserGroup, Users, Department

# ----------------------------
# List User Groups
# ----------------------------
def user_groups(request):
    groups = UserGroup.objects.all()
    departments = Department.objects.all()
    users = Users.objects.all()
    context = {
        'groups': groups,
        'departments': departments,
        'users': users,
    }
    return render(request, 'user_groups.html', context)

# ----------------------------
# Add User Group
# ----------------------------
def add_user_group(request):
    if request.method == "POST":
        name = request.POST.get("name")
        department_id = request.POST.get("department")
        department = Department.objects.get(pk=department_id) if department_id else None

        group = UserGroup.objects.create(name=name, department=department)
        messages.success(request, f'User Group "{group.name}" created successfully.')
    return redirect('user_groups')

# ----------------------------
# Edit User Group
# ----------------------------
def edit_user_group(request, group_id):
    group = get_object_or_404(UserGroup, pk=group_id)
    if request.method == "POST":
        group.name = request.POST.get("name")
        department_id = request.POST.get("department")
        group.department = Department.objects.get(pk=department_id) if department_id else None
        group.save()
        messages.success(request, f'User Group "{group.name}" updated successfully.')
    return redirect('user_groups')

# ----------------------------
# Delete User Group
# ----------------------------
def delete_user_group(request, group_id):
    group = get_object_or_404(UserGroup, pk=group_id)
    group.delete()
    messages.success(request, f'User Group "{group.name}" deleted successfully.')
    return redirect('user_groups')

# ----------------------------
# Assign Users to Group
# ----------------------------
def assign_users_group(request, group_id):
    group = get_object_or_404(UserGroup, pk=group_id)
    if request.method == "POST":
        user_ids = request.POST.getlist("users")  # Multi-select
        group.users.set(user_ids)  # Replace existing users with selected
        messages.success(request, f'Users assigned to "{group.name}" successfully.')
    return redirect('user_groups')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Users, Department
from django.utils import timezone

# Master user list
def master_user(request):
    users = Users.objects.all().select_related("department")
    departments = Department.objects.all()
    return render(request, "master_user.html", {"users": users, "departments": departments})


# Add new user
def add_user(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        title = request.POST.get("title")
        department_id = request.POST.get("department_id")
        role = request.POST.get("role")
        is_active = True if request.POST.get("is_active") == "on" else False

        department = get_object_or_404(Department, department_id=department_id)

        Users.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            title=title,
            department=department,
            role=role,
            is_active=is_active,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        messages.success(request, f"User '{full_name}' updated successfully!")
        return redirect("master_user")


# Edit user
def edit_user(request, user_id):
    user = get_object_or_404(Users, user_id=user_id)
    departments = Department.objects.all()

    if request.method == "POST":
        user.full_name = request.POST.get("full_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.title = request.POST.get("title")
        department_id = request.POST.get("department_id")
        user.department = get_object_or_404(Department, department_id=department_id)
        user.role = request.POST.get("role")
        user.is_active = True if request.POST.get("is_active") == "on" else False
        user.updated_at = timezone.now()
        user.save()
        messages.success( request,f"User '{user.full_name}' updated successfully!")
        return redirect("master_user")

    return render(request, "edit_user.html", {"user": user, "departments": departments})


# Copy user (duplicate entry)
def copy_user(request, user_id):
    user = get_object_or_404(Users, user_id=user_id)
    user.pk = None  # remove primary key
    user.full_name = f"{user.full_name} (Copy)"
    user.email = f"copy_{user.email}"
    user.created_at = timezone.now()
    user.updated_at = timezone.now()
    user.save()
    messages.success(request, "User copied successfully.")
    return redirect("master_user")


# Delete user
def delete_user(request, user_id):
    user = get_object_or_404(Users, user_id=user_id)
    user.delete()
    messages.success(request,  f"User '{user.full_name}' Deleted successfully!")
    return redirect("master_user")


from django.shortcuts import render, redirect, get_object_or_404
from .models import Location, LocationFamily, LocationType, Floor, Building
from django.db.models import Q
from django.contrib import messages

# -------------------------------
# Locations List & Filter
# -------------------------------
def locations_list(request):
    locations = Location.objects.all()
    families = LocationFamily.objects.all()
    types = LocationType.objects.all()
    floors = Floor.objects.all()
    buildings = Building.objects.all()

    # Filters
    family_filter = request.GET.get('family')
    type_filter = request.GET.get('type')
    floor_filter = request.GET.get('floor')
    building_filter = request.GET.get('building')

    if family_filter:
        locations = locations.filter(family_id=family_filter)
    if type_filter:
        locations = locations.filter(type_id=type_filter)
    if floor_filter:
        locations = locations.filter(floor_id=floor_filter)
    if building_filter:
        locations = locations.filter(building_id=building_filter)

    context = {
        'locations': locations,
        'families': families,
        'types': types,
        'floors': floors,
        'buildings': buildings,
        'selected_family': family_filter,
        'selected_type': type_filter,
        'selected_floor': floor_filter,
        'selected_building': building_filter,
    }
    return render(request, 'locations_list.html', context)


# -------------------------------
# Add/Edit Location
# -------------------------------
def location_form(request, location_id=None):
    if location_id:
        location = get_object_or_404(Location, pk=location_id)
    else:
        location = None

    families = LocationFamily.objects.all()
    types = LocationType.objects.all()
    floors = Floor.objects.all()
    buildings = Building.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        family = request.POST.get('family') or None
        loc_type = request.POST.get('type') or None
        floor = request.POST.get('floor') or None
        building = request.POST.get('building') or None
        room_no = request.POST.get('room_no')
        pavilion = request.POST.get('pavilion')
        capacity = request.POST.get('capacity') or None

        if location:
            location.name = name
            location.family_id = family
            location.type_id = loc_type
            location.floor_id = floor
            location.building_id = building
            location.room_no = room_no
            location.pavilion = pavilion
            location.capacity = capacity
            location.save()
        else:
            Location.objects.create(
                name=name,
                family_id=family,
                type_id=loc_type,
                floor_id=floor,
                building_id=building,
                room_no=room_no,
                pavilion=pavilion,
                capacity=capacity
            )
        messages.success(request,f"Location {name} successfully!")
        return redirect('locations_list')

    context = {
        'location': location,
        'families': families,
        'types': types,
        'floors': floors,
        'buildings': buildings,
    }
    
    return render(request, 'location_form.html', context)


# -------------------------------
# Delete Location
# -------------------------------
def location_delete(request, location_id):
    location = get_object_or_404(Location, pk=location_id)
    location_name=location.name
    location.delete()
    messages.success(request,f"Location {location_name} deleted successfully")
    return redirect('locations_list')

from django.shortcuts import render, redirect, get_object_or_404
from .models import RequestType, RequestFamily, WorkFamily, Workflow, Checklist
from django.contrib import messages
# -------------------------
# List Request Types
# -------------------------
def request_types_list(request):
    request_types = RequestType.objects.all()

    # Optional: filter by request_family or work_family
    family_id = request.GET.get('request_family')
    work_family_id = request.GET.get('work_family')
    request_families = RequestFamily.objects.all()

    if family_id:
        request_types = request_types.filter(request_family_id=family_id)
    if work_family_id:
        request_types = request_types.filter(work_family_id=work_family_id)

    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()

    context = {
        'request_types': request_types,
        'families': families,
        'work_families': work_families,
        'selected_family': family_id,
        'selected_work_family': work_family_id,
        "request_families": request_families,
    }
    return render(request, 'request_types_list.html', context)


# -------------------------
# Add Request Type
# -------------------------
def request_type_add(request):
    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()
    workflows = Workflow.objects.all()
    checklists = Checklist.objects.all()
    request_families = RequestFamily.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        workflow_id = request.POST.get('workflow')
        work_family_id = request.POST.get('work_family')
        request_family_id = request.POST.get('request_family')
        checklist_id = request.POST.get('checklist')
        active = True if request.POST.get('active') == 'on' else False

        workflow = Workflow.objects.get(pk=workflow_id) if workflow_id else None
        work_family = WorkFamily.objects.get(pk=work_family_id) if work_family_id else None
        request_family = RequestFamily.objects.get(pk=request_family_id) if request_family_id else None
        checklist = Checklist.objects.get(pk=checklist_id) if checklist_id else None

        RequestType.objects.create(
            name=name,
            workflow=workflow,
            work_family=work_family,
            request_family=request_family,
            checklist=checklist,
            active=active
        )
        messages.success(request,f"Request {name} is added successfully!")
        return redirect('request_types_list')

    context = {
        'families': families,
        'work_families': work_families,
        'workflows': workflows,
        'checklists': checklists,
        "request_families": request_families,
        'request_type': None
    }
    return render(request, 'request_type_form.html', context)


# -------------------------
# Edit Request Type
# -------------------------
def request_type_edit(request, request_type_id):
    request_type = get_object_or_404(RequestType, pk=request_type_id)
    families = RequestFamily.objects.all()
    work_families = WorkFamily.objects.all()
    workflows = Workflow.objects.all()
    checklists = Checklist.objects.all()
    request_families = RequestFamily.objects.all()

    if request.method == 'POST':
        request_type.name = request.POST.get('name')
        workflow_id = request.POST.get('workflow')
        work_family_id = request.POST.get('work_family')
        request_family_id = request.POST.get('request_family')
        checklist_id = request.POST.get('checklist')
        request_type.active = True if request.POST.get('active') == 'on' else False

        request_type.workflow = Workflow.objects.get(pk=workflow_id) if workflow_id else None
        request_type.work_family = WorkFamily.objects.get(pk=work_family_id) if work_family_id else None
        request_type.request_family = RequestFamily.objects.get(pk=request_family_id) if request_family_id else None
        request_type.checklist = Checklist.objects.get(pk=checklist_id) if checklist_id else None

        request_type.save()
        messages.success(request,f"Request {request_type.name} is updated successfully!")
        return redirect('request_types_list')

    context = {
        'request_type': request_type,
        'families': families,
        'work_families': work_families,
        'workflows': workflows,
        'checklists': checklists,
        "request_families": request_families,
    }
    return render(request, 'request_type_form.html', context)


# -------------------------
# Delete Request Type
# -------------------------
def request_type_delete(request, request_type_id):
    request_type = get_object_or_404(RequestType, pk=request_type_id)
    request_type_name=request_type.name
    request_type.delete()
    messages.success(request,f"Request {request_type_name} is added successfully!")
    return redirect('request_types_list')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Checklist, ChecklistItem, Location
from django.contrib import messages
# --- Checklists ---

@login_required
def checklist_list(request):
    checklists = Checklist.objects.all()
    return render(request, "list.html", {"checklists": checklists})

@login_required
def add_checklist(request):
    locations = Location.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        location_id = request.POST.get("location")
        location = Location.objects.get(pk=location_id) if location_id else None
        Checklist.objects.create(name=name, location=location)
        messages.success(request,f"Checklist {name} added successfully!")
        return redirect("checklist_list")
    return render(request, "add_edit.html", {"locations": locations})

@login_required
def edit_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    locations = Location.objects.all()
    if request.method == "POST":
        checklist.name = request.POST.get("name")
        location_id = request.POST.get("location")
        checklist.location = Location.objects.get(pk=location_id) if location_id else None
        checklist.save()
        messages.success(request,f"Checklist {checklist.name} updated successfully!")
        return redirect("checklist_list")
    return render(request, "add_edit.html", {"checklist": checklist, "locations": locations})

@login_required
def delete_checklist(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    checklist_name=checklist.name
    checklist.delete()
    messages.success(request,f"Checklist {checklist_name} added successfully!")
    return redirect("checklist_list")

# --- Checklist Items ---

@login_required
def add_item(request, checklist_id):
    checklist = get_object_or_404(Checklist, checklist_id=checklist_id)
    if request.method == "POST":
        label = request.POST.get("label")
        required = bool(request.POST.get("required"))
        ChecklistItem.objects.create(checklist=checklist, label=label, required=required)
        messages.success(request,f"Item {label} added successfully!")
        return redirect("checklist_list")
    return render(request, "add_item.html", {"checklist": checklist})

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(ChecklistItem, item_id=item_id)
    if request.method == "POST":
        item.label = request.POST.get("label")
        item.required = bool(request.POST.get("required"))
        item.save()
        messages.success(request,f"Item {item.label} updated successfully!")
        return redirect("checklist_list")
    return render(request, "edit_item.html", {"item": item})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(ChecklistItem, item_id=item_id)
    item_label=item.label
    item.delete()
    messages.success(request,f"Item  {item_label} deleted successfully!")
    return redirect("checklist_list")
# app1/views.py (append these imports + views)
import io, base64, qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Count, DateField
from django.db.models.functions import TruncDate, ExtractHour

from .models import Voucher, RedemptionLog

# ---------- Helper to build absolute URL ----------
def full_url(request, path):
    return request.build_absolute_uri(path)

# ---------- Reception check-in: create voucher + QR ----------
import qrcode
import io
import base64
from urllib.parse import quote
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Voucher
import qrcode
import io
import base64
from urllib.parse import quote
from datetime import datetime
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Voucher
import datetime

def _parse_yyyy_mm_dd(s: str):
    """Return date object or None. Accepts '', None, or 'YYYY-MM-DD'."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        # If you prefer to show an error instead, return an error message here.
        return None
# ---------- Reception check-in: create voucher + QR ----------
import qrcode
import io
from django.core.files.base import ContentFile
from django.urls import reverse
@login_required
def create_voucher_checkin(request):
    if request.method == "POST":
        guest_name = request.POST.get("guest_name")
        room_no = request.POST.get("room_no")
        adults = int(request.POST.get("adults", 1))
        kids = int(request.POST.get("kids", 0))
        quantity = int(request.POST.get("quantity", 0))
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        check_in_date = _parse_yyyy_mm_dd(request.POST.get("check_in_date"))
        check_out_date = _parse_yyyy_mm_dd(request.POST.get("check_out_date"))
        include_breakfast = request.POST.get("include_breakfast") == "on"  # checkbox

        # ✅ Create voucher first
        voucher = Voucher.objects.create(
            guest_name=guest_name,
            room_no=room_no,
            phone_number=phone_number,
            email=email,
            adults=adults,
            kids=kids,
            quantity=quantity,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            include_breakfast=include_breakfast,
        )

        # Generate landing URL using voucher_code
        voucher_page_url = reverse("voucher_landing", args=[voucher.voucher_code])
        landing_url = request.build_absolute_uri(voucher_page_url)

        # Generate scan URL for QR
        scan_url = request.build_absolute_uri(reverse("scan_voucher", args=[voucher.voucher_code]))

        # Generate QR code
        qr_content = voucher.voucher_code  # you can customize
        qr = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")

        # Save QR code as base64 string
        qr_img_str = base64.b64encode(buffer.getvalue()).decode()
        voucher.qr_code = qr_img_str

        # Save QR code as image file
        file_name = f"voucher_{voucher.id}.png"
        voucher.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

        voucher.save()

        # Absolute URL for QR sharing
        qr_absolute_url = request.build_absolute_uri(voucher.qr_code_image.url)

        return render(request, "voucher_success.html", {
            "voucher": voucher,
            "qr_absolute_url": qr_absolute_url,
            "include_breakfast": include_breakfast,
            "scan_url": scan_url,
            "landing_url": landing_url,
        })

    return render(request, "checkin_form.html")

from django.shortcuts import get_object_or_404

@login_required
def voucher_landing(request, voucher_code):
    voucher = get_object_or_404(Voucher, voucher_code=voucher_code)
    return render(request, "voucher_landing.html", {
        "voucher": voucher,
        "qr_absolute_url": request.build_absolute_uri(voucher.qr_code_image.url),
    })
  

import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from .models import Voucher
from django.utils import timezone
import pandas as pd

def breakfast_voucher_report(request):
    vouchers = Voucher.objects.all().values()
    df = pd.DataFrame(vouchers)

    # ✅ Convert timezone-aware datetimes to naive datetimes
    for col in df.select_dtypes(include=['datetimetz']).columns:
        df[col] = df[col].dt.tz_localize(None)

    if request.GET.get("export") == "1":
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="vouchers.xlsx"'
        df.to_excel(response, index=False)
        return response

    return render(request, "breakfast_voucher_report.html", {"vouchers": vouchers})

from django.utils.timezone import now

@login_required
def mark_checkout(request, voucher_id):
    try:
        voucher = Voucher.objects.get(id=voucher_id)
    except Voucher.DoesNotExist:
        return HttpResponse("Voucher not found", status=404)

    # Update check-out date with today's date
    voucher.check_out_date = now().date()
    voucher.save()

    return redirect("checkin_form")
  # Or any page you like


# ---------- Public voucher detail (for link clicks) ----------
def voucher_detail_public(request, voucher_id):
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    # Show voucher info and status
    return render(request, "voucher_detail.html", {"voucher": voucher})

# ---------- Scanner API (used by restaurant staff) ----------
@require_POST
@login_required
def scan_voucher_api(request):
    """
    POST data can contain: voucher_code OR voucher_id
    This endpoint validates and redeems if allowed.
    Returns JSON {success, message, redeemed, voucher_id, guest_name, room_no}
    """
    code = request.POST.get("voucher_code")
    vid = request.POST.get("voucher_id")

    if not code and not vid:
        return JsonResponse({"success": False, "message": "voucher_code or voucher_id required."}, status=400)

    try:
        if code:
            voucher = Voucher.objects.get(voucher_code=code)
        else:
            voucher = Voucher.objects.get(pk=int(vid))
    except Voucher.DoesNotExist:
        # Log failed attempt
        RedemptionLog.objects.create(voucher=None if not vid else None, success=False, scanner_ip=request.META.get("REMOTE_ADDR"), note="Voucher not found")
        return JsonResponse({"success": False, "message": "Voucher not found."}, status=404)

    # Create a log stub; we'll update note/success later
    log = RedemptionLog.objects.create(voucher=voucher, scanned_by=request.user if request.user.is_authenticated else None, scanner_ip=request.META.get("REMOTE_ADDR"))

    # Validate
    if not voucher.is_valid_now():
        log.success = False
        log.note = "Expired / out of validity period"
        log.save(update_fields=["success", "note"])
        return JsonResponse({"success": False, "message": "Voucher expired / not valid today."}, status=400)

    if voucher.redeemed:
        log.success = False
        log.note = "Already redeemed"
        log.save(update_fields=["success", "note"])
        return JsonResponse({"success": False, "message": "Voucher already redeemed."}, status=400)

    # Redeem now
    voucher.mark_redeemed(user=request.user if request.user.is_authenticated else None)
    log.success = True
    log.note = "Redeemed successfully"
    log.save(update_fields=["success", "note"])

    return JsonResponse({
        "success": True,
        "message": "Voucher redeemed.",
        "redeemed": True,
        "voucher_id": voucher.id,
        "voucher_code": voucher.voucher_code,
        "guest_name": voucher.guest_name,
        "room_no": voucher.room_no,
        "redeemed_at": voucher.redeemed_at,
    })

# ---------- Reporting APIs / Views ----------
@login_required
def report_redemptions_per_day(request):
    """
    Example: ?start=YYYY-MM-DD&end=YYYY-MM-DD (defaults: last 7 days)
    Returns JSON or renders simple template if request.is_ajax=false
    """
    from django.utils.dateparse import parse_date
    end = parse_date(request.GET.get("end")) or timezone.localdate()
    start = parse_date(request.GET.get("start")) or (end - timezone.timedelta(days=6))

    qs = RedemptionLog.objects.filter(success=True, scanned_at__date__range=(start, end))
    day_counts = qs.annotate(day=TruncDate("scanned_at")).values("day").annotate(total=Count("log_id")).order_by("day")

    data = {str(x["day"]): x["total"] for x in day_counts}
    # if non-ajax render template
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"start": str(start), "end": str(end), "daily": data})
    return render(request, "report_redemptions.html", {"start": start, "end": end, "daily": data})

@login_required
def report_skipped_guests(request):
    """
    Guests who had vouchers in a date range but no successful redemption.
    """
    from django.utils.dateparse import parse_date
    end = parse_date(request.GET.get("end")) or timezone.localdate()
    start = parse_date(request.GET.get("start")) or (end - timezone.timedelta(days=6))

    vouchers = Voucher.objects.filter(created_at__date__range=(start, end))
    redeemed_voucher_ids = RedemptionLog.objects.filter(success=True, voucher__in=vouchers).values_list("voucher_id", flat=True).distinct()
    skipped = vouchers.exclude(id__in=redeemed_voucher_ids)

    return render(request, "report_skipped.html", {"start": start, "end": end, "skipped": skipped})

@login_required
def report_peak_times(request):
    """
    Aggregates redemption logs by hour to find peak breakfast times.
    Returns JSON or template.
    """
    end = request.GET.get("end")
    start = request.GET.get("start")
    # Simple last 7 days default
    end_date = timezone.localdate()
    start_date = end_date - timezone.timedelta(days=6)

    qs = RedemptionLog.objects.filter(success=True, scanned_at__date__range=(start_date, end_date))
    hours = qs.annotate(hour=ExtractHour("scanned_at")).values("hour").annotate(total=Count("log_id")).order_by("hour")

    data = {h["hour"]: h["total"] for h in hours}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"start": str(start_date), "end": str(end_date), "hours": data})
    return render(request, "report_peak.html", {"hours": data, "start": start_date, "end": end_date})
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

def scan_voucher(request, code):
    voucher = get_object_or_404(Voucher, voucher_code=code)

    if voucher.is_used:
        return render(request, "voucher_expired.html", {"voucher": voucher})

    # Mark as used on first scan
    voucher.is_used = True
    voucher.save()

    return render(request, "voucher_valid.html", {"voucher": voucher, "scanned_at": timezone.now()})
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Voucher
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from .models import Voucher

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from .models import Voucher

@api_view(["GET"])
def validate_voucher(request):
    code = request.GET.get("code")
    if not code:
        return Response({"message": "Voucher code is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return Response({"message": "Invalid voucher code."}, status=status.HTTP_404_NOT_FOUND)

    # 1. Expired after check-out
    if voucher.is_expired():
        return Response({"message": "❌ Voucher has expired."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Valid & not used yet
    if voucher.is_valid_today():
        voucher.mark_scanned_today()
        return Response({"message": "✅ Voucher redeemed successfully for today."})

    # 3. Already used or not valid date
    return Response(
        {"message": "❌ Voucher already used today or not valid for today."},
        status=status.HTTP_400_BAD_REQUEST,
    )


   
@login_required
def scan_voucher_page(request):
    return render(request, "scan_voucher.html")

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def mark_whatsapp_sent(request, voucher_id):
    try:
        voucher = Voucher.objects.get(id=voucher_id)
        voucher.qr_sent_whatsapp = True
        voucher.save()
        return JsonResponse({"success": True})
    except Voucher.DoesNotExist:
        return JsonResponse({"success": False}, status=404)


from django.http import JsonResponse
from django.db.models import Count


@login_required
def complaint_summary(request):
    """
    Returns a JSON summary of complaint counts grouped by status.
    Example:
    {
      "NEW": 5,
      "ACCEPTED": 2,
      "ON_HOLD": 3,
      "CLOSED": 7
    }
    """

    is_admin = request.user.is_staff or request.user.is_superuser

    if is_admin:
        complaints = Complaint.objects.all()
    else:
        complaints = Complaint.objects.filter(user=request.user)

    summary = (
        complaints.values("status")
        .annotate(total=Count("id"))
        .order_by()
    )

    # Convert queryset into dictionary with all statuses
    result = {status: 0 for status, _ in Complaint.STATUS_CHOICES}
    for row in summary:
        result[row["status"]] = row["total"]

    return JsonResponse(result)

# app/views.py
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import ExtractHour, TruncDate
import datetime, json

from .models import (
    ServiceRequest, RequestType, Location, Users,
    WorkFamily, RequestFamily, Department,
    LocationFamily, Floor, Building, LocationType
)

def _parse_date_safe(s):
    d = parse_date(s) if s else None
    return d

def service_report(request):
    # -------------------- Dates --------------------
    start = _parse_date_safe(request.GET.get("start"))
    end = _parse_date_safe(request.GET.get("end"))

    if not start:
        start = timezone.localdate() - datetime.timedelta(days=30)
    if not end:
        end = timezone.localdate()

    # inclusive end date for __date range
    base_qs = ServiceRequest.objects.select_related(
        "request_type", "location", "requester_user", "assignee_user",
        "location__building", "location__floor"
    ).filter(created_at__date__range=(start, end))

    # -------------------- Filters --------------------
    # NOTE: use your model PK names carefully (…_id on FKs)
    raw = request.GET

    filters = {
        "request_type__request_family_id": raw.get("request_family"),
        "request_type__work_family_id": raw.get("work_family"),
        "request_type_id": raw.get("request_type"),
        "status": raw.get("status"),
        "requester_user_id": raw.get("requester"),
        "assignee_user_id": raw.get("owner"),
        "requester_user__department_id": raw.get("requester_dept"),
        "assignee_user__department_id": raw.get("owner_dept"),
        "location_id": raw.get("location"),
        "location__family_id": raw.get("location_family"),
        "location__floor_id": raw.get("floor"),
        "location__building_id": raw.get("building"),
    }
    filters = {k: v for k, v in filters.items() if v}
    qs = base_qs.filter(**filters)

    # toggles
    pending_only = raw.get("pending_only")
    on_hold = raw.get("on_hold")
    priority_only = raw.get("priority")  # just an example; change to your priority values
    if pending_only:
        qs = qs.filter(status__iexact="Pending")
    if on_hold:
        qs = qs.filter(status__iexact="On Hold")
    if priority_only:
        qs = qs.exclude(priority__isnull=True).exclude(priority__exact="")

    # -------------------- Cards (by Request Type) --------------------
    # Show a card per Request Type (like Housekeeping, Concierge, etc.)
    card_rows = (
        qs.values("request_type__name")
          .annotate(total=Count("request_id"))
          .order_by("request_type__name")
    )
    pending_rows = (
        qs.filter(status__iexact="Pending")
          .values("request_type__name")
          .annotate(pending=Count("request_id"))
    )
    pend_map = {r["request_type__name"]: r["pending"] for r in pending_rows}

    dept_cards = []
    for r in card_rows:
        name = r["request_type__name"] or "Uncategorized"
        total = r["total"]
        pending = pend_map.get(name, 0)
        pct = round((pending / total * 100) if total else 0, 2)
        dept_cards.append({"name": name, "total": total, "pending_percent": pct})

    # Ensure some cards exist even if no data, so UI looks consistent
    if not dept_cards and RequestType.objects.exists():
        for rt in RequestType.objects.all()[:8]:
            dept_cards.append({"name": rt.name, "total": 0, "pending_percent": 0})

    # -------------------- Top-10 tables --------------------
    top_requesters = (
        qs.values("requester_user__full_name")
          .annotate(total=Count("request_id"))
          .order_by("-total")[:10]
    )
    top_owners = (
        qs.values("assignee_user__full_name")
          .annotate(total=Count("request_id"))
          .order_by("-total")[:10]
    )
    top_locations = (
        qs.values("location__name")
          .annotate(total=Count("request_id"))
          .order_by("-total")[:10]
    )

    # -------------------- Charts --------------------
    # Hourly
    hourly_q = (
        qs.annotate(hour=ExtractHour("created_at"))
          .values("hour").annotate(total=Count("request_id"))
          .order_by("hour")
    )
    hourly_data = [{"hour": int(r["hour"]), "total": r["total"]} for r in hourly_q if r["hour"] is not None]

    # Daily
    daily_q = (
        qs.annotate(day=TruncDate("created_at"))
          .values("day").annotate(total=Count("request_id"))
          .order_by("day")
    )
    daily_data = [{"day": r["day"].isoformat() if r["day"] else None, "total": r["total"]} for r in daily_q]

    # Family (pie) – group by Request Family
    family_q = (
        qs.values("request_type__request_family__name")
          .annotate(total=Count("request_id")).order_by()
    )
    family_data = [
        {"label": r["request_type__request_family__name"] or "Other", "total": r["total"]}
        for r in family_q
    ]

    # -------------------- List (paginated) --------------------
    paginator = Paginator(qs.order_by("-created_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # -------------------- Context --------------------
    ctx = {
        # filters / dropdowns
        "request_families": RequestFamily.objects.order_by("name"),
        "work_families": WorkFamily.objects.order_by("name"),
        "request_types": RequestType.objects.order_by("name"),
        "owners": Users.objects.filter(is_active=True).order_by("full_name"),
        "requesters": User.objects.filter(is_active=True).order_by("username"),
        "departments": Department.objects.order_by("name"),
        "locations": Location.objects.order_by("name"),
        "location_families": LocationFamily.objects.order_by("name"),
        "floors": Floor.objects.order_by("building__name", "floor_number"),
        "buildings": Building.objects.order_by("name"),
        "location_types": LocationType.objects.order_by("name"),

        # raw values for form
        "start": start.isoformat(),
        "end": end.isoformat(),

        # cards
        "dept_cards": dept_cards,

        # tables
        "top_requesters": top_requesters,
        "top_owners": top_owners,
        "top_locations": top_locations,

        # list
        "page_obj": page_obj,

        # chart JSON blobs (avoid template loops in JS)
        "hourly_json": json.dumps(hourly_data),
        "daily_json": json.dumps(daily_data),
        "family_json": json.dumps(family_data),
    }
    return render(request, "service_report.html", ctx)


import io
import qrcode
import base64
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import GymMember, GymVisitor, GymVisit
from .forms import GymMemberForm, GymVisitorForm


# ======================
# MEMBER
# ======================
@login_required
def add_member(request):
    if request.method == "POST":
        form = GymMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)

            # Generate QR
            qr_img = qrcode.make(member.customer_code)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_data = base64.b64encode(buffer.getvalue()).decode()
            member.qr_code = member.customer_code
            member.qr_code_image = f"data:image/png;base64,{qr_data}"
            member.save()
            return redirect("member_list")
    else:
        form = GymMemberForm()
    return render(request, "add_member.html", {"form": form})


@login_required
def member_list(request):
    members = GymMember.objects.all()
    return render(request, "member_list.html", {"members": members})


@login_required
def export_members(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=members.csv"
    writer = csv.writer(response)
    writer.writerow([
        "Customer ID", "Name", "Phone", "Email", "City", "Start Date", "End Date", "Status"
    ])
    for m in GymMember.objects.all():
        writer.writerow([m.customer_code, m.full_name, m.phone, m.email, m.city, m.start_date, m.end_date, m.status])
    return response


# ======================
# VISITOR
# ======================
@login_required
def visitor_check(request):
    if request.method == "POST":
        member_id = request.POST.get("member_id")
        try:
            member = GymMember.objects.get(customer_code=member_id)
            return render(request, "gym/visitor_check.html", {"member": member})
        except GymMember.DoesNotExist:
            return render(request, "gym/visitor_check.html", {"error": "Member not found"})
    return render(request, "visitor_check.html")


@login_required
def visitor_register(request):
    if request.method == "POST":
        form = GymVisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save()
            GymVisit.objects.create(visitor=visitor, checked_by_user=request.user, visit_at=now())
            return redirect("visit_report")
    else:
        form = GymVisitorForm()
    return render(request, "visitor_register.html", {"form": form})


# ======================
# VISIT REPORT
# ======================
@login_required
def visit_report(request):
    visits = GymVisit.objects.select_related("member", "visitor", "checked_by_user").all().order_by("-visit_at")
    return render(request, "visit_report.html", {"visits": visits})


@login_required
def export_visits(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=visits.csv"
    writer = csv.writer(response)
    writer.writerow(["ID", "Customer ID", "Name", "Date Time", "Admin"])
    for v in GymVisit.objects.all():
        member_code = v.member.customer_code if v.member else ""
        name = v.member.full_name if v.member else (v.visitor.full_name if v.visitor else "")
        writer.writerow([v.visit_id, member_code, name, v.visit_at, v.checked_by_user.username])
    return response
# ... keep previous imports and functions ...

@login_required
def edit_member(request, member_id):
    member = get_object_or_404(GymMember, pk=member_id)
    if request.method == "POST":
        form = GymMemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save(commit=False)
            # Update QR if customer_code changed
            if member.customer_code and (not member.qr_code or member.customer_code != member.qr_code):
                import io, qrcode, base64
                qr_img = qrcode.make(member.customer_code)
                buffer = io.BytesIO()
                qr_img.save(buffer, format="PNG")
                qr_data = base64.b64encode(buffer.getvalue()).decode()
                member.qr_code = member.customer_code
                member.qr_code_image = f"data:image/png;base64,{qr_data}"
            member.save()
            return redirect("member_list")
    else:
        form = GymMemberForm(instance=member)
    return render(request, "edit_member.html", {"form": form, "member": member})


@login_required
def delete_member(request, member_id):
    member = get_object_or_404(GymMember, pk=member_id)
    if request.method == "POST":
        member.delete()
        return redirect("member_list")
    return render(request, "delete_member.html", {"member": member})

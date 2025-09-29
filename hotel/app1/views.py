import os
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .tasks import send_notification
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
from .models import GymVisit, UserProfile, Voucher

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

# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Department
# from django.contrib import messages

# def department_list(request):
#     departments = Department.objects.all()
#     return render(request, "departments.html", {"departments": departments})

# def add_department(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         description = request.POST.get('description', '') 
#         if name:
#             Department.objects.create(name=name, description=description)
#         messages.success(request,f"Department {name} added successfully!")
#         return redirect("department_list")

# def edit_department(request, pk):
#     department = get_object_or_404(Department, pk=pk)
#     if request.method == "POST":
#         name = request.POST.get("name")
#         description = request.POST.get('description', '')
#         if name:
#             department.name = name
#             department.description = description
#             department.save()
#         messages.success(request,f"Department {department.name} updated successfully!")
#         return redirect("department_list")
#     # ❌ Remove the render line (no separate template)
#     return redirect("department_list")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .models import Department, Complaint
from django.contrib.auth.models import User

# ===== Departments =====
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Department

def department_list(request):
    departments = Department.objects.all().select_related("lead")
    users = User.objects.all().order_by("username")          # for dropdown
    return render(request, "departments.html", {
        "departments": departments,
        "users": users,
    })

def add_department(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        lead_id = request.POST.get("lead")
        if name:
            Department.objects.create(
                name=name,
                description=description,
                lead_id=lead_id if lead_id else None,
            )
            messages.success(request, f"Department {name} added successfully!")
        return redirect("department_list")

def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        lead_id = request.POST.get("lead")
        if name:
            department.name = name
            department.description = description
            department.lead_id = lead_id if lead_id else None
            department.save()
            messages.success(request,
                f"Department {department.name} updated successfully!")
        return redirect("department_list")
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
# @login_required
# def complaint_list(request):
#     statuses = ["Pending", "Assigned", "Accepted", "In Progress", "Completed", "Escalated", "Closed", "All"]
#     status_filter = request.GET.get("status", "Pending")

#     # Check if the user is admin/staff
#     is_admin = request.user.is_staff or request.user.is_superuser

#     # Complaints queryset
#     if is_admin:
#         complaints = Complaint.objects.all()
#         users = User.objects.all()  # Admin can see all users
#     else:
#         complaints = Complaint.objects.filter(user=request.user)
#         users = [request.user]  # Normal users see only themselves

#     # Apply status filter
#     if status_filter == "All":
#         complaints = complaints
#     elif status_filter == "Closed":
#         complaints = complaints.filter(status="CLOSED")
#     elif status_filter == "On Hold":
#         complaints = complaints.filter(status="ON_HOLD")
#     else:  # Pending = NEW or ACCEPTED
#         complaints = complaints.exclude(status="CLOSED")

#     return render(request, "complaints.html", {
#         "complaints": complaints,
#         "users": users,
#         "statuses": statuses,
#         "status_filter": status_filter,
#         "is_admin": is_admin
#     })


# @login_required
# def add_complaint(request):
#     if request.method == "POST":
#         department_id = request.POST.get("department_id")
#         department = Department.objects.get(id=department_id)
#         user = request.user

#         complaint = Complaint.objects.create(
#             user=user,
#             department=department,
#             title=request.POST["title"],
#             description=request.POST["description"],
#             location=request.POST["location"],
#         )

#         # Notify department lead
#         leads = User.objects.filter(is_staff=True, department=department)
#         for lead in leads:
#             send_notification.delay(lead.id, f"New complaint {complaint.id} in your department: {complaint.location}")

#         messages.success(request, "Complaint raised successfully.")
#     return redirect("complaint_list")
# @login_required
# def assign_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)
#     if request.method == "POST":
#         team_member_id = request.POST.get("team_member_id")
#         member = User.objects.get(id=team_member_id)
#         complaint.owner = member
#         complaint.status = "ASSIGNED"
#         complaint.save()

#         # Notify team member
#         send_notification.delay(member.id, f"You've been assigned complaint {complaint.id}. Please accept.")
#     return redirect("complaint_list")
# @login_required
# def accept_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)
#     if request.user != complaint.owner:
#         messages.error(request, "Not authorized")
#         return redirect("complaint_list")

#     complaint.status = "ACCEPTED"
#     complaint.sla_start = timezone.now()
#     complaint.save()

#     # Notify lead
#     send_notification.delay(complaint.department.user.id, f"{request.user.username} accepted complaint {complaint.id}")
#     return redirect("complaint_list")

# @login_required
# def complete_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)
#     if request.user != complaint.owner:
#         messages.error(request, "Not authorized")
#         return redirect("complaint_list")

#     complaint.status = "COMPLETED"
#     complaint.sla_end = timezone.now()
#     complaint.save()

#     # Notify lead and front desk
#     leads = User.objects.filter(is_staff=True, department=complaint.department)
#     for lead in leads:
#         send_notification.delay(lead.id, f"Complaint {complaint.id} completed by {request.user.username}")
#     send_notification.delay(complaint.user.id, f"Your complaint {complaint.id} has been resolved")
#     return redirect("complaint_list")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Complaint, Department
from django.contrib.auth.models import User

# app1/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Complaint, Department, User
from .tasks import send_notification   # your celery task or helper
# complaints/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Complaint, Department
from .tasks import send_notification   # your Celery task
from app1 import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Complaint, Department, User
from .tasks import send_notification  # Celery task

# STATUSES = [
#     "PENDING", "ASSIGNED", "ACCEPTED", "IN_PROGRESS",
#     "COMPLETED", "ESCALATED", "REJECTED", "CLOSED"
# ]

# def is_admin(user):
#     return user.is_superuser or user.is_staff

# @login_required
# def complaint_list(request):
#     status_filter = request.GET.get("status", "All")
#     unread_count = request.user.notification_set.filter(is_read=False).count()
#     notifications = request.user.notification_set.all()[:5]

#     if is_admin(request.user):
#         # Admin: see all complaints
#         complaints = Complaint.objects.all().order_by("-created_on")
#     else:
#         # Normal users, department leads, and assigned members
#         complaints = Complaint.objects.filter(
#             Q(user=request.user) |
#             Q(owner=request.user) |
#             Q(assigned_to=request.user) |
#             Q(department__lead=request.user)
#         ).order_by("-created_on")

#     if status_filter and status_filter != "All":
#         complaints = complaints.filter(status=status_filter)

#     context = {
#         "complaints": complaints,
#         "statuses": STATUSES,
#         "status_filter": status_filter,
#         "departments": Department.objects.all(),
#         "users": User.objects.all(),
#         "notifications": notifications,
#         "unread_count": unread_count,
#         "team_members": User.objects.filter(is_staff=True),
#         "is_admin": is_admin(request.user),
#     }
#     return render(request, "complaints.html", context)

# @login_required
# def add_complaint(request):
#     if request.method == "POST":
#         user_id = request.POST.get("user_id")
#         department_id = request.POST.get("department_id")
#         location = request.POST.get("location")
#         title = request.POST.get("title")
#         description = request.POST.get("description")

#         if not all([user_id, department_id, location, title, description]):
#             messages.error(request, "All fields are required!")
#             return redirect("complaint_list")

#         user = get_object_or_404(User, id=user_id)
#         department = get_object_or_404(Department, department_id=department_id)

#         lead = department.lead
#         status = "ASSIGNED" if lead else "PENDING"

#         complaint = Complaint.objects.create(
#             user=user,
#             department=department,
#             owner=lead,  # Lead becomes initial owner
#             location=location,
#             title=title,
#             description=description,
#             status=status,
#             created_on=timezone.now()
#         )

#         if lead:
#             send_notification.delay(
#                 lead.id,
#                 f"New complaint #{complaint.id} automatically assigned to you as Department Lead."
#             )

#         messages.success(
#             request,
#             f"Complaint '{title}' created and assigned to Department Lead." if lead
#             else f"Complaint '{title}' created (no lead assigned)."
#         )
#         return redirect("complaint_list")

#     messages.error(request, "Invalid request method.")
#     return redirect("complaint_list")
# @login_required
# def assign_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)

#     # Only department lead can assign
#     if request.user != complaint.department.lead:
#         messages.error(request, "Only the Department Lead can assign team members.")
#         return redirect("complaint_list")

#     if request.method == "POST":
#         team_member_id = request.POST.get("team_member_id")
#         if not team_member_id:
#             messages.error(request, "Select a team member.")
#             return redirect("complaint_list")

#         member = get_object_or_404(User, id=team_member_id)

#         # Assign complaint to team member
#         complaint.assigned_to = member   # <-- Correct column
#         complaint.status = "ASSIGNED"
#         complaint.save()

#         # Notify the assigned member
#         send_notification.delay(
#             member.id,
#             f"You have been assigned complaint #{complaint.id} by the Department Lead."
#         )

#         messages.success(request, f"Complaint #{complaint.id} assigned to {member.username}.")
#         return redirect("complaint_list")

#     messages.error(request, "Invalid request method.")
#     return redirect("complaint_list")





# @login_required
# def accept_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)

#     # Only the assigned member can accept
#     if request.user != complaint.assigned_to:
#         messages.error(request, "You are not authorized to accept this complaint.")
#         return redirect('complaint_list')

#     complaint.status = 'ACCEPTED'
#     complaint.sla_start = timezone.now()
#     complaint.save()

#     # Notify department lead
#     if complaint.department and complaint.department.lead:
#         send_notification.delay(
#             complaint.department.lead.id,
#             f"Team member {request.user.username} has accepted complaint #{complaint.id}. SLA started."
#         )

#     messages.success(request, f"Complaint #{complaint.id} accepted by {request.user.username}.")
#     return redirect('complaint_list')



# @login_required
# def complete_complaint(request, complaint_id):
#     complaint = get_object_or_404(Complaint, id=complaint_id)

#     if request.user != complaint.assigned_to:
#         messages.error(request, "You are not authorized to complete this complaint.")
#         return redirect('complaint_list')

#     if request.method == "POST":
#         picture = request.FILES.get("picture")
#         complaint.status = "COMPLETED"
#         complaint.completed_on = timezone.now()
#         if picture:
#             complaint.picture = picture
#         complaint.save()

#         send_notification.delay(
#             complaint.user.id,
#             f"Your complaint #{complaint.id} has been completed by {request.user.username}."
#         )

#         messages.success(request, f"Complaint #{complaint.id} completed successfully.")
#         return redirect('complaint_list')

#     return redirect('complaint_list')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import Complaint, Department, Notification, User
from .tasks import send_notification

STATUSES = ["PENDING", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "ESCALATED", "REJECTED", "CLOSED"]

def is_admin(user):
    return user.is_superuser or user.is_staff

# ------------------- Complaint List -------------------
@login_required
def complaint_list(request):
    status_filter = request.GET.get("status", "All")
    unread_count = request.user.notification_set.filter(is_read=False).count()
    notifications = request.user.notification_set.order_by("-created_on")[:5]
    complaints = Complaint.objects.all()
    now = timezone.now()

    for c in complaints:
        if c.sla_start and c.due_date:
            total_seconds = (c.due_date - c.sla_start).total_seconds()
            elapsed_seconds = (now - c.sla_start).total_seconds()
            # Ensure progress is between 0% and 100%
            c.progress = max(0, min(100, (elapsed_seconds / total_seconds) * 100))
        else:
            c.progress = None
    if is_admin(request.user):
        complaints = Complaint.objects.all().order_by("-created_on")
    else:
        complaints = Complaint.objects.filter(
            Q(user=request.user) |
            Q(owner=request.user) |
            Q(assigned_to=request.user) |
            Q(department__lead=request.user)
        ).order_by("-created_on")

    if status_filter and status_filter != "All":
        complaints = complaints.filter(status=status_filter)

    context = {
        "complaints": complaints,
        "statuses": STATUSES,
        "status_filter": status_filter,
        "departments": Department.objects.all(),
        "users": User.objects.all(),
        "notifications": notifications,
        "unread_count": unread_count,
        "team_members": User.objects.filter(is_staff=True),
        "is_admin": is_admin(request.user),
        "now":now,
    }
    return render(request, "complaints.html", context)

# ------------------- Add Complaint -------------------
@login_required
def add_complaint(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        department_id = request.POST.get("department_id")
        location = request.POST.get("location")
        title = request.POST.get("title")
        description = request.POST.get("description")

        if not all([user_id, department_id, location, title, description]):
            messages.error(request, "All fields are required!")
            return redirect("complaint_list")

        user = get_object_or_404(User, id=user_id)
        department = get_object_or_404(Department, department_id=department_id)

        lead = department.lead
        status = "ASSIGNED" if lead else "PENDING"

        complaint = Complaint.objects.create(
            user=user,
            department=department,
            owner=lead,
            location=location,
            title=title,
            description=description,
            status=status,
            created_on=timezone.now()
        )

        if lead:
            send_notification.delay(
                lead.id,
                f"New complaint #{complaint.id} automatically assigned to you as Department Lead."
            )

        messages.success(
            request,
            f"Complaint '{title}' created and assigned to Department Lead." if lead
            else f"Complaint '{title}' created (no lead assigned)."
        )
        return redirect("complaint_list")

    messages.error(request, "Invalid request method.")
    return redirect("complaint_list")

# ------------------- Assign Complaint -------------------
@login_required
def assign_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.user != complaint.department.lead:
        messages.error(request, "Only the Department Lead can assign team members.")
        return redirect("complaint_list")

    if request.method == "POST":
        team_member_id = request.POST.get("team_member_id")
        if not team_member_id:
            messages.error(request, "Select a team member.")
            return redirect("complaint_list")

        member = get_object_or_404(User, id=team_member_id)

        complaint.assigned_to = member
        complaint.status = "ASSIGNED"
        complaint.save()

        send_notification.delay(
            member.id,
            f"You have been assigned complaint #{complaint.id} by the Department Lead."
        )

        messages.success(request, f"Complaint #{complaint.id} assigned to {member.username}.")
        return redirect("complaint_list")

    messages.error(request, "Invalid request method.")
    return redirect("complaint_list")

# ------------------- Accept Complaint -------------------
@login_required
def accept_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.user != complaint.assigned_to:
        messages.error(request, "You are not authorized to accept this complaint.")
        return redirect('complaint_list')

    complaint.status = 'ACCEPTED'
    complaint.sla_start = timezone.now()
    complaint.save()

    if complaint.department and complaint.department.lead:
        send_notification.delay(
            complaint.department.lead.id,
            f"Team member {request.user.username} has accepted complaint #{complaint.id}. SLA started."
        )

    messages.success(request, f"Complaint #{complaint.id} accepted by {request.user.username}.")
    return redirect('complaint_list')

# ------------------- Complete Complaint -------------------
@login_required
def complete_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.user != complaint.assigned_to:
        messages.error(request, "You are not authorized to complete this complaint.")
        return redirect('complaint_list')

    if request.method == "POST":
        picture = request.FILES.get("picture")
        complaint.status = "COMPLETED"
        complaint.completed_on = timezone.now()
        complaint.sla_end = timezone.now()  # Stop SLA timer
        if picture:
            complaint.picture = picture
        complaint.save()

        send_notification.delay(
            complaint.user.id,
            f"Your complaint #{complaint.id} has been completed by {request.user.username}."
        )

        messages.success(request, f"Complaint #{complaint.id} completed successfully.")
        return redirect('complaint_list')

    return redirect('complaint_list')

# ------------------- Notification API -------------------
@login_required
def get_notifications(request):
    notifications = request.user.notification_set.order_by("-created_on")[:5]
    unread_count = request.user.notification_set.filter(is_read=False).count()

    notif_list = []
    for n in notifications:
        notif_list.append({
            "id": n.id,
            "message": n.message[:50],
            "created_on": n.created_on.strftime("%d-%b-%Y %H:%M"),
            "is_read": n.is_read
        })

    return JsonResponse({"notifications": notif_list, "unread_count": unread_count})

@login_required
def mark_notifications_read(request):
    request.user.notification_set.filter(is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})



# ------------------ Update Complaint Status (Admin) ------------------
@login_required
def update_complaint_status(request, complaint_id, action):
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to perform this action.")
        return redirect("complaint_list")

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if action == "close":
        complaint.status = "CLOSED"
        complaint.due_date = timezone.now()
        complaint.save()
        send_notification.delay(
            complaint.user.id,
            f"Complaint #{complaint.id} has been closed. SLA: {complaint.sla_start} - {complaint.due_date}"
        )
        messages.success(request, f"Complaint #{complaint.id} closed.")
    else:
        messages.error(request, "Invalid action.")
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
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def get_notifications(request):
    notifications = request.user.notification_set.all()[:5]
    unread_count = request.user.notification_set.filter(is_read=False).count()
    
    notif_list = []
    for n in notifications:
        notif_list.append({
            "id": n.id,
            "message": n.message[:50],
            "created_on": n.created_on.strftime("%d-%b-%Y %H:%M"),
            "is_read": n.is_read
        })

    return JsonResponse({"notifications": notif_list, "unread_count": unread_count})


@login_required
def mark_notifications_read(request):
    request.user.notification_set.filter(is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserGroup, Users, Department
from django.contrib.auth.models import User
# ----------------------------
# List User Groups
# ----------------------------
def user_groups(request):
    groups = UserGroup.objects.all()
    departments = Department.objects.all()
    users = User.objects.all()
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

# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib import messages
# from .models import Users, Department
# from django.utils import timezone
# from django.contrib.auth.models import User

# # Master user list
# def master_user(request):
#     users = User.objects.all()
#     departments = Department.objects.all()
#     return render(request, "master_user.html", {"users": users, "departments": departments})

# from django.contrib.auth.models import User
# # Add new user
# def add_user(request):
    
#     if request.method == "POST":
#         username = request.POST.get("username")
#         email = request.POST.get("email")
#         phone = request.POST.get("phone")
#         title = request.POST.get("title")
#         password=request.POST.get("password")
#         department_id = request.POST.get("department_id")
#         role = request.POST.get("role")
#         is_active = True if request.POST.get("is_active") == "on" else False

#         department = get_object_or_404(Department, department_id=department_id)
#         user = User.objects.create_user(
#             username=username,
#             email=email,
#             password=password,
#             is_active=is_active
#         )

#         UserProfile.objects.create(
#             user=user,
#             phone=phone,
#             title=title,
#             department=department,
            
#             role=role,
#             # is_active=is_active,
#             # created_at=timezone.now(),
#             # updated_at=timezone.now()
#         )
#         messages.success(request, f"User '{username}' updated successfully!")
#         return redirect("master_user")


# # Edit user
# def edit_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     departments = Department.objects.all()

#     if request.method == "POST":
#         user.username = request.POST.get("username")
#         user.email = request.POST.get("email")
#         user.phone = request.POST.get("phone")
#         user.title = request.POST.get("title")
#         department_id = request.POST.get("department_id")
#         user.department = get_object_or_404(Department, department_id=department_id)
#         user.role = request.POST.get("role")
#         user.is_active = True if request.POST.get("is_active") == "on" else False
#         user.updated_at = timezone.now()
#         user.save()
#         messages.success( request,f"User '{user.username}' updated successfully!")
#         return redirect("master_user")

#     return render(request, "edit_user.html", {"user": user, "departments": departments})


# # Copy user (duplicate entry)
# def copy_user(request, user_id):
#     user = get_object_or_404(User, user_id=user_id)
#     user.pk = None  # remove primary key
#     user.full_name = f"{user.full_name} (Copy)"
#     user.email = f"copy_{user.email}"
#     user.created_at = timezone.now()
#     user.updated_at = timezone.now()
#     user.save()
#     messages.success(request, "User copied successfully.")
#     return redirect("master_user")


# # Delete user
# def delete_user(request, user_id):
#     # Get the user object
#     user = get_object_or_404(User, id=user_id)

#     # Optional: delete the linked UserProfile first
#     try:
#         profile = UserProfile.objects.get(user=user)
#         profile.delete()
#     except UserProfile.DoesNotExist:
#         pass  # No profile to delete, continue

#     # Delete the user
#     user.delete()

#     messages.success(request, f"User '{user.username}' deleted successfully!")
#     return redirect("master_user")

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import UserProfile, Department


# Master user list
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Q

def master_user(request):
    users = User.objects.all().select_related("profile")
    departments = Department.objects.all()

    # Filters
    search = request.GET.get("search", "").strip()
    role_filter = request.GET.get("role", "")
    dept_filter = request.GET.get("department", "")
    status_filter = request.GET.get("status", "")

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__phone__icontains=search)
        )

    if role_filter and role_filter != "all":
        users = users.filter(profile__role__iexact=role_filter)

    if dept_filter:
        users = users.filter(profile__department_id=dept_filter)

    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)
    total_users = User.objects.count()
    # Pagination
    page_number = request.GET.get("page", 1)
    paginator = Paginator(users, 5)  # 5 users per page
    page_obj = paginator.get_page(page_number)

    return render(request, "master.html", {
        "users": page_obj,
        "departments": departments,
        "role_filter": role_filter,
        "dept_filter": dept_filter,
        "status_filter": status_filter,
        "paginator": paginator,
        "page_number": int(page_number),
        "total_users":total_users,
        
    })


# Add new user
def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        title = request.POST.get("title")
        password = request.POST.get("password")
        department_id = request.POST.get("department_id")
        role = request.POST.get("role")
        is_active = True if request.POST.get("is_active") == "on" else False

        department = get_object_or_404(Department, department_id=department_id)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=is_active
        )

        UserProfile.objects.create(
            user=user,
            phone=phone,
            title=title,
            department=department,
            role=role,
        )
        messages.success(request, f"User '{username}' added successfully!")
        return redirect("master_user")


# Edit user
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)

    departments = Department.objects.all()

    if request.method == "POST":
        # update user fields
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.is_active = "is_active" in request.POST
        user.save()

        # update profile fields
        profile.phone = request.POST.get("phone")
        profile.title = request.POST.get("title")
        profile.role = request.POST.get("role")
        department_id = request.POST.get("department_id")
        if department_id:
            profile.department = Department.objects.get(pk=department_id)
        profile.save()

        messages.success(request, "User updated successfully!")
        return redirect("master_user")

    return render(request, "edit_user.html", {
        "user": user,
        "departments": departments,
    })


# Copy user
def copy_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    new_user = User.objects.create_user(
        username=f"{user.username}_copy",
        email=f"copy_{user.email}",
        password="password123",  # set default password
        is_active=user.is_active
    )

    UserProfile.objects.create(
        user=new_user,
        phone=profile.phone,
        title=profile.title,
        department=profile.department,
        role=profile.role,
    )

    messages.success(request, f"User '{user.username}' copied successfully.")
    return redirect("master_user")


# Delete user
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"User '{username}' deleted successfully!")
    return redirect("master_user")

import csv
from django.http import HttpResponse
from django.db.models import Q
from .models import User, Department

def export_users(request):
    users = User.objects.all().select_related('profile')

    # Filters same as master_user view
    search = request.GET.get("search", "").strip()
    role_filter = request.GET.get("role", "")
    dept_filter = request.GET.get("department", "")
    status_filter = request.GET.get("status", "")

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__phone__icontains=search)
        )

    if role_filter and role_filter != "all":
        users = users.filter(profile__role__iexact=role_filter)

    if dept_filter:
        users = users.filter(profile__department_id=dept_filter)

    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Role', 'Department', 'Status'])

    for user in users:
        role = getattr(user.profile, 'role', '')
        dept = getattr(user.profile.department, 'name', '') if getattr(user.profile, 'department', None) else ''
        status = 'Active' if user.is_active else 'Inactive'
        writer.writerow([user.username, user.email, role, dept, status])

    return response

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.conf import settings
import os, uuid

# @csrf_exempt
# @staff_member_required  # Only admin can upload for others
# def upload_avatar(request):
#     """
#     Upload avatar for a specific user (user_id must be sent in POST).
#     Replaces only that user's old avatar, leaves all others unchanged.
#     """
#     if request.method == "POST" and request.FILES.get("avatar"):
#         user_id = request.POST.get("user_id") or request.GET.get("user_id")
#         if not user_id:
#             return JsonResponse({"error": "Missing user_id"}, status=400)

#         try:
#             target_user = User.objects.get(pk=user_id)
#             profile = target_user.profile
#         except User.DoesNotExist:
#             return JsonResponse({"error": "User not found"}, status=404)

#         file = request.FILES["avatar"]

#         # delete old file if exists
#         if profile.avatar_url:
#             old_path = profile.avatar_url.replace(settings.MEDIA_URL, "")
#             if default_storage.exists(old_path):
#                 default_storage.delete(old_path)

#         # save new file with unique name
#         ext = os.path.splitext(file.name)[1]
#         unique_name = f"{target_user.id}_{uuid.uuid4().hex}{ext}"
#         filename = default_storage.save(os.path.join("avatars", unique_name), file)
#         file_url = default_storage.url(filename)

#         profile.avatar_url = file_url
#         profile.save(update_fields=["avatar_url"])

#         return JsonResponse({"url": file_url, "user_id": user_id})

#     return JsonResponse({"error": "No file provided"}, status=400)


import os
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib.auth.models import User
from app1.models import UserProfile  # import your profile model

@csrf_exempt
@staff_member_required  # Only admin can upload for others
def upload_avatar(request):
    """
    Upload avatar for a specific user (user_id must be sent in POST).
    Creates UserProfile if missing. Replaces old avatar.
    """
    if request.method == "POST" and request.FILES.get("avatar"):
        user_id = request.POST.get("user_id") or request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Missing user_id"}, status=400)

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        # Get or create UserProfile
        profile, created = UserProfile.objects.get_or_create(user=target_user)

        file = request.FILES["avatar"]

        # delete old avatar if exists
        if profile.avatar_url:
            old_path = profile.avatar_url.replace(settings.MEDIA_URL, "")
            if default_storage.exists(old_path):
                default_storage.delete(old_path)

        # save new file with unique name
        ext = os.path.splitext(file.name)[1]
        unique_name = f"{target_user.id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join("avatars", unique_name)
        filename = default_storage.save(path, file)

        # store persistent URL
        profile.avatar_url = default_storage.url(filename)
        profile.save(update_fields=["avatar_url"])

        return JsonResponse({"url": profile.avatar_url, "user_id": user_id})

    return JsonResponse({"error": "No file provided"}, status=400)


from django.shortcuts import render, redirect, get_object_or_404
from .models import Location, LocationFamily, LocationType, Floor, Building
from django.db.models import Q
from django.contrib import messages

# -------------------------------
# Locations List & Filter
# -------------------------------
# def locations_list(request):
#     locations = Location.objects.all()
#     families = LocationFamily.objects.all()
#     types = LocationType.objects.all()
#     floors = Floor.objects.all()
#     buildings = Building.objects.all()

#     # Filters
#     family_filter = request.GET.get('family')
#     type_filter = request.GET.get('type')
#     floor_filter = request.GET.get('floor')
#     building_filter = request.GET.get('building')

#     if family_filter:
#         locations = locations.filter(family_id=family_filter)
#     if type_filter:
#         locations = locations.filter(type_id=type_filter)
#     if floor_filter:
#         locations = locations.filter(floor_id=floor_filter)
#     if building_filter:
#         locations = locations.filter(building_id=building_filter)

#     context = {
#         'locations': locations,
#         'families': families,
#         'types': types,
#         'floors': floors,
#         'buildings': buildings,
#         'selected_family': family_filter,
#         'selected_type': type_filter,
#         'selected_floor': floor_filter,
#         'selected_building': building_filter,
#     }
#     return render(request, 'locations_list.html', context)

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
    search_query = request.GET.get('search')

    if family_filter:
        locations = locations.filter(family_id=family_filter)
    if type_filter:
        locations = locations.filter(type_id=type_filter)
    if floor_filter:
        locations = locations.filter(floor_id=floor_filter)
    if building_filter:
        locations = locations.filter(building_id=building_filter)
    if search_query:
        locations = locations.filter(name__icontains=search_query) 

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
        'search_query': search_query,
    }
    return render(request, 'location.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import LocationFamily, LocationType


# def location_manage_view(request, family_id):
#     """Main page to manage a single LocationFamily."""
#     family = get_object_or_404(LocationFamily, family_id=family_id)

#     all_location_types = family.types.all()
#     first_three = all_location_types[:3]
#     remaining_count = max(all_location_types.count() - 3, 0)

#     locations_with_status = [
#         {"name": loc.name, "status": "Active" if loc.is_active else "Inactive"}
#         for loc in first_three
#     ]

#     context = {
#         "family": family,
#         "locations": locations_with_status,
#         "remaining_count": remaining_count,
#         # if you store a checklist model, fetch it here.
#         "default_checklist": {"name": "Room Service"},
#     }
#     return render(request, "location_manage.html", context)


# @require_http_methods(["POST"])
# def add_family(request):
#     """
#     Create a new LocationFamily from a form or AJAX POST.
#     Expects a field 'name'.
#     """
#     name = request.POST.get("name", "").strip()
#     if not name:
#         return JsonResponse({"error": "Name is required"}, status=400)

#     family = LocationFamily.objects.create(name=name)
#     return JsonResponse({"success": True, "family_id": family.id, "family_name": family.name})


# def search_families(request):
#     """
#     Returns JSON list of families matching a ?q= search.
#     """
#     query = request.GET.get("q", "").strip()
#     results = LocationFamily.objects.filter(name__icontains=query) if query else []
#     return JsonResponse({
#         "results": [{"id": f.id, "name": f.name} for f in results]
#     })

# app1/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import LocationFamily, LocationType, Checklist
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

# app1/views.py
from django.shortcuts import render, get_object_or_404
from .models import LocationFamily, LocationType, Checklist

def location_manage_view(request, family_id=None):
    """
    If family_id is provided, show that family's details.
    Otherwise, show all families.
    """
    default_checklist = Checklist.objects.first()

    if family_id:
        family = get_object_or_404(LocationFamily, family_id=family_id)
        locations = family.types.all()  # related_name='types'
        remaining_count = max(0, locations.count() - 5)  # show "+N more" if needed
        context = {
            'families': [family],
            'locations': locations[:5],
            'remaining_count': remaining_count,
            'default_checklist': default_checklist
        }
    else:
        families = LocationFamily.objects.prefetch_related('types').all()
        context = {
            'families': families,
            'default_checklist': default_checklist
        }

    return render(request, 'location_management.html', context)



def search_locations(request):
    """
    Search for location types by name.
    Returns JSON results.
    """
    query = request.GET.get('q', '')
    results = []

    if query:
        location_types = LocationType.objects.filter(name__icontains=query)
        for loc in location_types:
            results.append({
                'id': loc.id,
                'name': loc.name,
                'family': loc.family.name,
                'status': 'Active' if loc.is_active else 'Inactive',
            })
    return JsonResponse({'results': results})


@csrf_exempt
def add_family(request):
    """
    Add a new location family via AJAX.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name cannot be empty.'})

        family, created = LocationFamily.objects.get_or_create(name=name)
        return JsonResponse({'success': True, 'family_id': family.id})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def bulk_import_locations(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        import csv
        import io
        decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
        for row in reader:
            Location.objects.create(
                name=row.get('name'),
                room_no=row.get('room_no'),
                pavilion=row.get('pavilion'),
                capacity=row.get('capacity') or None,
                family_id=row.get('family_id') or None,
                type_id=row.get('type_id') or None,
                floor_id=row.get('floor_id') or None,
                building_id=row.get('building_id') or None
            )
        messages.success(request, "CSV imported successfully!")
        return redirect("locations_list")
    messages.error(request, "No file selected!")
    return redirect("locations_list")


import csv
from django.http import HttpResponse
from .models import Location

@login_required
def export_locations_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="locations.csv"'

    writer = csv.writer(response)
    # Write header
    writer.writerow(['Name', 'Room No', 'Pavilion', 'Capacity', 'Family', 'Type', 'Floor', 'Building'])

    # Write data
    locations = Location.objects.all()
    for loc in locations:
        writer.writerow([
            loc.name,
            loc.room_no,
            loc.pavilion,
            loc.capacity,
            loc.family.name if loc.family else '',
            loc.type.name if loc.type else '',
            loc.floor.floor_number if loc.floor else '',
            loc.building.name if loc.building else ''
        ])

    return response

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
# -------------------------------
# Location Families
# -------------------------------
def families_list(request):
    families = LocationFamily.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        LocationFamily.objects.create(name=name)
        messages.success(request, "Family added successfully!")
        return redirect("locations_list")
    return families

def family_delete(request, family_id):
    family = get_object_or_404(LocationFamily, pk=family_id)
    family.delete()
    messages.success(request, "Family deleted successfully!")
    return redirect("locations_list")


# -------------------------------
# Location Types
# -------------------------------
def types_list(request):
    types = LocationType.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        LocationType.objects.create(name=name)
        messages.success(request, "Type added successfully!")
        return redirect("locations_list")
    return types

def type_delete(request, type_id):
    t = get_object_or_404(LocationType, pk=type_id)
    t.delete()
    messages.success(request, "Type deleted successfully!")
    return redirect("locations_list")


# -------------------------------
# Floors
# -------------------------------
def floors_list(request):
    floors = Floor.objects.all()
    if request.method == "POST":
        name = request.POST.get("floor_name")
        floor_number = request.POST.get("floor_number") or 0
        Floor.objects.create(floor_name=name, floor_number=floor_number)
        messages.success(request, "Floor added successfully!")
        return redirect("locations_list")
    return floors

def floor_delete(request, floor_id):
    f = get_object_or_404(Floor, pk=floor_id)
    f.delete()
    messages.success(request, "Floor deleted successfully!")
    return redirect("locations_list")


# -------------------------------
# Buildings
# -------------------------------
def buildings_list(request):
    buildings = Building.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        Building.objects.create(name=name)
        messages.success(request, "Building added successfully!")
        return redirect("locations_list")
    return buildings

def building_delete(request, building_id):
    b = get_object_or_404(Building, pk=building_id)
    b.delete()
    messages.success(request, "Building deleted successfully!")
    return redirect("locations_list")
# -------------------------------
# Location Families
# -------------------------------
def family_form(request, family_id=None):
    if family_id:
        family = get_object_or_404(LocationFamily, pk=family_id)
    else:
        family = None

    if request.method == "POST":
        name = request.POST.get("name")

        if family:
            family.name = name
            family.save()
            messages.success(request, "Family updated successfully!")
        else:
            LocationFamily.objects.create(name=name)
            messages.success(request, "Family added successfully!")

        return redirect("locations_list")

    context = {"family": family}
    return render(request, "family_form.html", context)





# -------------------------------
# Location Types
# -------------------------------
def type_form(request, type_id=None):
    if type_id:
        loc_type = get_object_or_404(LocationType, pk=type_id)
    else:
        loc_type = None

    if request.method == "POST":
        name = request.POST.get("name")

        if loc_type:
            loc_type.name = name
            loc_type.save()
            messages.success(request, "Type updated successfully!")
        else:
            LocationType.objects.create(name=name)
            messages.success(request, "Type added successfully!")

        return redirect("locations_list")

    context = {"loc_type": loc_type}
    return render(request, "type_form.html", context)

# views.py
from django.shortcuts import render
from .models import Building

def building_cards(request):
    buildings = Building.objects.all()
    return render(request, 'building.html', {'buildings': buildings})




# -------------------------------
# Floors
# -------------------------------
def floor_form(request, floor_id=None):
    if floor_id:
        floor = get_object_or_404(Floor, pk=floor_id)
    else:
        floor = None
    
    if request.method == "POST":
        name = request.POST.get("floor_name")
        floor_number = request.POST.get("floor_number") or 0
        building_id = request.POST.get('building_id')
        building = Building.objects.get(building_id=building_id)
        if floor:
            floor.floor_name = name
            floor.floor_number = floor_number
            floor.building=building
            floor.save()
            messages.success(request, "Floor updated successfully!")
        else:
            Floor.objects.create(floor_name=name, floor_number=floor_number,building=building)
            messages.success(request, "Floor added successfully!")

        return redirect("locations_list")
    buildings = Building.objects.all()
        

    context = {"floor": floor,  'buildings': buildings}
    return render(request, "floor_form.html", context)





# -------------------------------
# Buildings
# -------------------------------
# def building_form(request, building_id=None):
#     if building_id:
#         building = get_object_or_404(Building, pk=building_id)
        
#     else:
#         building = None

#     if request.method == "POST":
#         name = request.POST.get("name")

#         if building:
#             building.name = name
#             building.save()
#             messages.success(request, "Building updated successfully!")
#         else:
#             Building.objects.create(name=name)
#             messages.success(request, "Building added successfully!")

#         return redirect("locations_list")

#     context = {"building": building}
#     return render(request, "building_form.html", context)

def building_form(request, building_id=None):
    if building_id:
        building = get_object_or_404(Building, pk=building_id)
    else:
        building = None

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        status = request.POST.get("status", "active")
        image = request.FILES.get("image")

        if building:
            building.name = name
            building.description = description
            building.status = status
            if image:
                building.image = image
            building.save()
            messages.success(request, "Building updated successfully!")
        else:
            Building.objects.create(
                name=name, description=description, status=status, image=image
            )
            messages.success(request, "Building added successfully!")

        return redirect("locations_list")

    return render(request, "building_form.html", {"building": building})

from django.shortcuts import get_object_or_404, redirect
from .models import Building

def upload_building_image(request, building_id):
    building = get_object_or_404(Building, building_id=building_id)
    if request.method == "POST" and request.FILES.get("image"):
        building.image = request.FILES["image"]
        building.save()
        messages.success(request, "Image uploaded successfully!")
    return redirect("building_cards")  # redirect to the building cards page



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import LocationFamily, LocationType, Floor, Building
def family_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            LocationFamily.objects.create(name=name)
            messages.success(request, "Family added successfully!")
            return redirect("locations_list")
    return render(request, "family_form.html")


def family_edit(request, family_id):
    family = get_object_or_404(LocationFamily, pk=family_id)
    if request.method == "POST":
        family.name = request.POST.get("name")
        family.save()
        messages.success(request, "Family updated successfully!")
        return redirect("locations_list")
    return render(request, "family_form.html", {"family": family})

def type_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            LocationType.objects.create(name=name)
            messages.success(request, "Type added successfully!")
            return redirect("locations_list")
    return render(request, "type_form.html")


def type_edit(request, type_id):
    t = get_object_or_404(LocationType, pk=type_id)
    if request.method == "POST":
        t.name = request.POST.get("name")
        t.save()
        messages.success(request, "Type updated successfully!")
        return redirect("locations_list")
    return render(request, "type_form.html", {"type": t})
def floor_add(request):
    if request.method == "POST":
        name = request.POST.get("floor_name")
        floor_number = request.POST.get("floor_number") or 0
        Floor.objects.create(floor_name=name, floor_number=floor_number)
        messages.success(request, "Floor added successfully!")
        return redirect("locations_list")
    return render(request, "floor_form.html")


def floor_edit(request, floor_id):
    floor = get_object_or_404(Floor, pk=floor_id)
    if request.method == "POST":
        floor.floor_name = request.POST.get("floor_name")
        floor.floor_number = request.POST.get("floor_number") or 0
        floor.save()
        messages.success(request, "Floor updated successfully!")
        return redirect("locations_list")
    return render(request, "floor_form.html", {"floor": floor})
def building_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Building.objects.create(name=name)
            messages.success(request, "Building added successfully!")
            return redirect("locations_list")
    return render(request, "building_form.html")


def building_edit(request, building_id):
    building = get_object_or_404(Building, pk=building_id)
    if request.method == "POST":
        building.name = request.POST.get("name")
        building.save()
        messages.success(request, "Building updated successfully!")
        return redirect("locations_list")
    return render(request, "building_form.html", {"building": building})


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
    checklists = Checklist.objects.annotate(
        required_items_count=Count('checklistitem', filter=Q(checklistitem__required=True))
    )

    # Active checklists are those with at least one required item
    active_checklists_count = checklists.filter(required_items_count__gt=0).count()

    return render(request, "list.html", {"checklists": checklists,"active_checklists_count":active_checklists_count})

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
from datetime import datetime, timedelta
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
    vouchers = Voucher.objects.all()
    df =  pd.DataFrame(Voucher.objects.all().values())

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

# @api_view(["GET"])
# def validate_voucher(request):
#     code = request.GET.get("code")
#     if not code:
#         return Response({"message": "Voucher code is required."}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         voucher = Voucher.objects.get(voucher_code=code)
#     except Voucher.DoesNotExist:
#         return Response({"message": "Invalid voucher code."}, status=status.HTTP_404_NOT_FOUND)

#     # 1. Expired after check-out
#     if voucher.is_expired():
#         return Response({"message": "❌ Voucher has expired."}, status=status.HTTP_400_BAD_REQUEST)

#     # 2. Valid & not used yet
#     if voucher.is_valid_today():
#         voucher.mark_scanned_today()
#         return Response({"message": "✅ Voucher redeemed successfully for today."})

#     # 3. Already used or not valid date
#     return Response(
#         {"message": "❌ Voucher already used today or not valid for today."},
#         status=status.HTTP_400_BAD_REQUEST,
#     )

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Voucher
from datetime import date

@api_view(["GET"])
def validate_voucher(request):
    """
    Validate a voucher when its QR code is scanned.
    Increments scan_count, updates redeemed flags, and
    returns status + updated fields.
    """
    code = request.GET.get("code")
    if not code:
        return Response({"message": "Voucher code is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return Response({"message": "Invalid voucher code."},
                        status=status.HTTP_404_NOT_FOUND)

    # 1. Expired?
    if voucher.is_expired():
        return Response({"message": "❌ Voucher has expired."},
                        status=status.HTTP_400_BAD_REQUEST)

    # 2. Valid for today?
    if voucher.is_valid_today():
        # ✅ increment scan_count and record history
        today = date.today().isoformat()
        if today not in (voucher.scan_history or []):
            voucher.scan_history.append(today)
        voucher.scan_count = (voucher.scan_count or 0) + 1

        # ✅ mark as redeemed (if not already)
        if not voucher.redeemed:
            voucher.redeemed = True
            voucher.redeemed_at = timezone.now()

        voucher.save(update_fields=["scan_history",
                                    "scan_count",
                                    "redeemed",
                                    "redeemed_at"])

        return Response({
            "success": True,
            "message": "✅ Voucher redeemed successfully for today.",
            "scan_count": voucher.scan_count,
            "redeemed": voucher.redeemed,
            "redeemed_at": voucher.redeemed_at,
        })

    # 3. Already used today or not valid
    return Response({
        "success": False,
        "message": "❌ Voucher already used today or not valid for today.",
        "scan_count": voucher.scan_count,
        "redeemed": voucher.redeemed,
        "redeemed_at": voucher.redeemed_at,
    }, status=status.HTTP_400_BAD_REQUEST)

   
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


# import io
# import qrcode
# import base64
# import csv
# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse
# from django.contrib.auth.decorators import login_required
# from django.utils.timezone import now
# from .models import GymMember, GymVisitor, GymVisit
# from .forms import GymMemberForm, GymVisitorForm


# # ======================
# # MEMBER
# # ======================
# from django.contrib import messages

# @login_required
# def add_member(request):
#     if request.method == "POST":
#         form = GymMemberForm(request.POST)
#         if form.is_valid():
#             member = form.save(commit=False)

#             # ✅ save pin as password field also
#             member.password = member.pin  

#             # ✅ Generate QR
#             import io, qrcode, base64
#             qr_img = qrcode.make(member.customer_code)
#             buffer = io.BytesIO()
#             qr_img.save(buffer, format="PNG")
#             qr_data = base64.b64encode(buffer.getvalue()).decode()
#             member.qr_code = member.customer_code
#             member.qr_code_image = f"data:image/png;base64,{qr_data}"

#             member.save()

#             # ✅ Success message
#             messages.success(request, f"Member '{member.full_name}' has been added successfully!")

#             return redirect("member_list")
#         else:
#             # form invalid → error messages automatically
#             messages.error(request, "Please correct the errors below.")
#     else:
#         form = GymMemberForm()
#     return render(request, "add_member.html", {"form": form})

# @login_required
# def edit_member(request, member_id):
#     member = get_object_or_404(GymMember, pk=member_id)
#     if request.method == "POST":
#         form = GymMemberForm(request.POST, instance=member)
#         if form.is_valid():
#             member = form.save(commit=False)

#             # ✅ Update QR if customer_code changed
#             if member.customer_code and (not member.qr_code or member.customer_code != member.qr_code):
#                 import io, qrcode, base64
#                 qr_img = qrcode.make(member.customer_code)
#                 buffer = io.BytesIO()
#                 qr_img.save(buffer, format="PNG")
#                 qr_data = base64.b64encode(buffer.getvalue()).decode()
#                 member.qr_code = member.customer_code
#                 member.qr_code_image = f"data:image/png;base64,{qr_data}"

#             member.save()
#             return redirect("member_list")
#     else:
#         form = GymMemberForm(instance=member)
#     return render(request, "edit_member.html", {"form": form, "member": member})



# @login_required
# def member_list(request):
#     members = GymMember.objects.all()
#     return render(request, "member_list.html", {"members": members})


# @login_required
# def export_members(request):
#     response = HttpResponse(content_type="text/csv")
#     response["Content-Disposition"] = "attachment; filename=members.csv"
#     writer = csv.writer(response)
#     writer.writerow([
#         "Customer ID", "Name", "Phone", "Email", "City", "Start Date", "End Date", "Status"
#     ])
#     for m in GymMember.objects.all():
#         writer.writerow([m.customer_code, m.full_name, m.phone, m.email, m.city, m.start_date, m.end_date, m.status])
#     return response


# # ======================
# # VISITOR
# # ======================
# @login_required
# def visitor_check(request):
#     if request.method == "POST":
#         member_id = request.POST.get("member_id")
#         try:
#             member = GymMember.objects.get(customer_code=member_id)
#             return render(request, "gym/visitor_check.html", {"member": member})
#         except GymMember.DoesNotExist:
#             return render(request, "gym/visitor_check.html", {"error": "Member not found"})
#     return render(request, "visitor_check.html")


# @login_required
# def visitor_register(request):
#     if request.method == "POST":
#         form = GymVisitorForm(request.POST)
#         if form.is_valid():
#             visitor = form.save()
#             GymVisit.objects.create(visitor=visitor, checked_by_user=request.user, visit_at=now())
#             return redirect("visit_report")
#     else:
#         form = GymVisitorForm()
#     return render(request, "visitor_register.html", {"form": form})


# # ======================
# # VISIT REPORT
# # ======================
# @login_required
# def visit_report(request):
#     visits = GymVisit.objects.select_related("member", "visitor", "checked_by_user").all().order_by("-visit_at")
#     return render(request, "visit_report.html", {"visits": visits})


# @login_required
# def export_visits(request):
#     response = HttpResponse(content_type="text/csv")
#     response["Content-Disposition"] = "attachment; filename=visits.csv"
#     writer = csv.writer(response)
#     writer.writerow(["ID", "Customer ID", "Name", "Date Time", "Admin"])
#     for v in GymVisit.objects.all():
#         member_code = v.member.customer_code if v.member else ""
#         name = v.member.full_name if v.member else (v.visitor.full_name if v.visitor else "")
#         writer.writerow([v.visit_id, member_code, name, v.visit_at, v.checked_by_user.username])
#     return response
# # ... keep previous imports and functions ...




# @login_required
# def delete_member(request, member_id):
#     member = get_object_or_404(GymMember, pk=member_id)
#     if request.method == "POST":
#         member.delete()
#         return redirect("member_list")
#     return render(request, "delete_member.html", {"member": member})
# views.py
import io, base64, qrcode
import pandas as pd
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import GymMember


# Generate unique code
def generate_customer_code():
    last = GymMember.objects.order_by("-member_id").first()
    if last:
        number = int(last.customer_code.replace("FGS", "")) + 1
    else:
        number = 1
    return f"FGS{number:04d}"


def add_member(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        nik = request.POST.get("nik")
        address = request.POST.get("address")
        city = request.POST.get("city")
        place_of_birth = request.POST.get("place_of_birth")
        date_of_birth = request.POST.get("date_of_birth") or None
        religion = request.POST.get("religion")
        gender = request.POST.get("gender")
        occupation = request.POST.get("occupation")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        pin = request.POST.get("pin")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "add_member.html",
                {"error": "Password and Confirm Password do not match."},
            )

        # Generate member code and dates
        customer_code = generate_customer_code()
        start_date = timezone.now().date()
        expiry_date = start_date + timedelta(days=90)

        # -----------------------------
        # QR-code logic (same as voucher)
        # -----------------------------
        # Content you want inside the QR
        

        # Save model first (without image file)
        member = GymMember.objects.create(
            customer_code=customer_code,
            full_name=full_name,
            nik=nik,
            address=address,
            city=city,
            place_of_birth=place_of_birth,
            date_of_birth=date_of_birth,
            religion=religion,
            gender=gender,
            occupation=occupation,
            phone=phone,
            email=email,
            pin=pin,
            password=password,
            confirm_password=confirm_password,
            start_date=start_date,
            expiry_date=expiry_date,
            status="Active",
             # store base64 string if desired
        )
        qr_content = member.customer_code

        # Generate PNG bytes
        qr_img = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")

        # Base64 string if you need it (optional)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Save actual PNG file to ImageField
        file_name = f"member_{member.member_id}.png"
        member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

        return redirect("member_list")

    return render(request, "add_member.html")
def member_list(request):
    members = GymMember.objects.all().order_by("-created_at")

    search = request.GET.get("search")
    if search:
        members = members.filter(
            Q(full_name__icontains=search) | Q(customer_code__icontains=search)
        )

    if request.GET.get("export") == "1":
        df = pd.DataFrame(members.values())
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_convert(None)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="members.xlsx"'
        df.to_excel(response, index=False)
        return response

    return render(request, "member_list.html", {"members": members})


    
# gym/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import GymMember

# @api_view(["GET"])
# def validate_member_qr(request):
#     code = (request.GET.get("code") or "").strip()
#     try:
#         member = GymMember.objects.get(customer_code=code)
#     except GymMember.DoesNotExist:
#         return Response({"message": "Invalid QR code."}, status=status.HTTP_404_NOT_FOUND)

#     if member.is_expired():
#         return Response({"message": "❌ Membership expired."}, status=status.HTTP_400_BAD_REQUEST)

#     # Try to mark scan
#     if member.mark_scanned_today(max_scans_per_day=3):
#         return Response({"success": True, "message": "✅ Entry allowed.", "scan_count": member.scan_count})

#     return Response({"success": False, "message": "❌ Daily scan limit reached."},
#                     status=status.HTTP_400_BAD_REQUEST)

# gym/views.py
from .models import GymMember, GymVisit
from django.contrib.auth.models import User

@api_view(["GET"])
def validate_member_qr(request):
    code = (request.GET.get("code") or "").strip()
    try:
        member = GymMember.objects.get(customer_code=code)
    except GymMember.DoesNotExist:
        return Response({"message": "Invalid QR code."}, status=status.HTTP_404_NOT_FOUND)

    # Check expiry
    if member.is_expired():
        return Response({"message": "❌ Membership expired."}, status=status.HTTP_400_BAD_REQUEST)

    # Try to mark scan
    if member.mark_scanned_today(max_scans_per_day=3):
        # ✅ Log into GymVisit table
        GymVisit.objects.create(
            member=member,
            checked_by_user=request.user,  # who scanned
            notes="QR Scan Entry"
        )
        return Response({
            "success": True,
            "message": "✅ Entry allowed.",
            "scan_count": member.scan_count
        })

    return Response({"success": False, "message": "❌ Daily scan limit reached."}, status=status.HTTP_400_BAD_REQUEST)

   
# gym/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def scan_gym_page(request):
    return render(request, "scan_gym.html")

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import GymMember
from django.utils import timezone
import qrcode, io, base64

# ---------- EDIT MEMBER ----------
from datetime import timedelta

def edit_member(request, member_id):
    member = get_object_or_404(GymMember, member_id=member_id)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        city = request.POST.get("city")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            messages.error(request, "❌ Password mismatch.")
            return render(request, "edit_member.html", {"member": member})

        # Update fields
        member.full_name = full_name
        member.address = address
        member.phone = phone
        member.email = email
        member.city = city
        if password:
            member.password = password
        
        # ✅ Extend voucher only if admin ticks/chooses "renew"
        renew = request.POST.get("renew_membership")  # from a checkbox in form
        if renew:
            if not member.is_expired():
                messages.warning(request, f"⚠️ {member.full_name} membership has not expired yet!")
                return render(request, "edit_member.html", {"member": member})
            today = timezone.now().date()
            member.start_date = today
            member.expiry_date = today + timedelta(days=90)  # 3 months
            member.qr_expired = False

            # 🔄 Re-generate QR
            qr_content = member.customer_code

        # Generate PNG bytes
            qr_img = qrcode.make(qr_content)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")

        # Base64 string if you need it (optional)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Save actual PNG file to ImageField
            file_name = f"member_{member.member_id}.png"
            member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

            

        # If inactive → expire QR
        if member.status == "Inactive":
            if member.qr_code_image:
                member.qr_code_image.delete(save=False)
            member.qr_code_image = None
            member.qr_expired = True

        member.save()
        messages.success(request, f"{member.full_name} ✅ Member updated successfully.")
        return redirect("member_list")

    return render(request, "edit_member.html", {"member": member})

# ---------- DELETE MEMBER ----------
def delete_member(request, member_id):
    member = get_object_or_404(GymMember, member_id=member_id)

    if request.method == "POST":
        member.delete()
        messages.success(request, "✅ Member deleted successfully.")
        return redirect("member_list")

    return render(request, "delete_member.html", {"member": member})

# gym/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q

@login_required
def gym_report(request):
    visits = GymVisit.objects.select_related("member", "visitor", "checked_by_user").order_by("-visit_at")

    # Date filter
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    if from_date and to_date:
        visits = visits.filter(visit_at__date__range=[from_date, to_date])

    # Export to Excel
    if request.GET.get("export") == "1":
        import pandas as pd
        df = pd.DataFrame(list(visits.values(
            "visit_id",
            "member__customer_code",
            "member__full_name",
            "visitor__full_name",
            "visit_at",
            "checked_by_user__username",
        )))
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="gym_report.xlsx"'
        # Convert all datetime columns to timezone-naive
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_localize(None)

        df.to_excel(response, index=False)
        return response

    return render(request, "gym_report.html", {"visits": visits})
from django.shortcuts import render
from django.contrib import messages
from .models import GymMember
from django.utils import timezone

def data_checker(request):
    result = None
    if request.method == "POST":
        member_id = request.POST.get("member_id")

        try:
            member = GymMember.objects.get(customer_code=member_id)
            today = timezone.now().date()

            if member.status == "Inactive":
                result = {"status": "Inactive ❌", "color_class": "success"}
            elif member.expiry_date and member.expiry_date < today:
                result = {"status": "Expired ⏳", "color_class": "success"}
            else:
                result = {"status": "Active ✅", "color_class": "success"}

            result["member"] = member

        except GymMember.DoesNotExist:
            messages.error(request, f"No member found with ID {member_id}")

    return render(request, "data_checker.html", {"result": result})

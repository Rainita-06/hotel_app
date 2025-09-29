from datetime import date, time, timedelta
from django.db import models


# =========================
# DEPARTMENT & USERS
# =========================
from django.contrib.auth.models import User
class Department(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100,blank=False, null=False)   # updated (was 120)
    description = models.CharField(max_length=255, null=True, blank=True)  
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)       # added

    class Meta:
        db_table = 'department'
    def __str__(self):
        return self.name

    @property
    def total_users(self):
        return Users.objects.filter(department=self).count()  

class Users(models.Model):  # changed to Users instead of User
    user_id = models.BigAutoField(primary_key=True) # updated (was BigAutoField PK)
    full_name = models.CharField(max_length=160,blank=False, null=False)   # updated (was full_name)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,blank=False, null=False)
    email = models.CharField(max_length=160, blank=True, null=True)
    phone = models.CharField(max_length=15,blank=False, null=False)
    title = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('employee', 'Employee')], default='employee')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'users'

from django.contrib.auth.models import User
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    title = models.CharField(max_length=120, blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=[('admin', 'Admin'), ('employee', 'Employee')],
        default='employee'
    )
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)
    

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return self.user.username


class UserGroup(models.Model):
    group_id = models.BigAutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, blank=False, null=False)
    users = models.ManyToManyField(User,related_name='user_groups',  # must add related_name
    blank=True,through='UserGroupMembership',   ) # updated
    name = models.CharField(max_length=120,blank=False, null=False)
    class Meta:
        db_table = 'user_group'


class UserGroupMembership(models.Model):
    user= models.ForeignKey(User, models.DO_NOTHING)
    group = models.ForeignKey(UserGroup, models.DO_NOTHING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_group_membership'
        unique_together = (('user', 'group'),)


# =========================
# LOCATIONS
# =========================

class Building(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
    ]
    building_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='building_images/', null=True, blank=True)  # NEW
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active') 

    class Meta:
        db_table = 'building'
    
    @property
    def floors_count(self):
        return self.floors.count()   # thanks to related_name='floors'

    @property
    def rooms_count(self):
        return self.locations.count()  

    


class Floor(models.Model):
    floor_name=models.CharField(max_length=50,blank=False,null=False)
    floor_id = models.BigAutoField(primary_key=True)
    building = models.ForeignKey('Building', models.DO_NOTHING,blank=False, null=False,related_name='floors')
    floor_number = models.IntegerField(blank=False, null=False)
    description = models.CharField(max_length=255, blank=True)  # e.g. “Lobby & Reception”
    rooms = models.PositiveIntegerField(default=0)
    occupancy = models.PositiveIntegerField(default=0)     # percent (0-100)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        db_table = 'floor'


class LocationFamily(models.Model):
    family_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)

    class Meta:
        db_table = 'location_family'


class LocationType(models.Model):
    type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)
    family = models.ForeignKey(LocationFamily, on_delete=models.CASCADE, related_name='types',null=False)
    is_active = models.BooleanField(default=True) 

    class Meta:
        db_table = 'location_type'


class Location(models.Model):
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('maintenance', 'Maintenance'),
]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    location_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50,blank=False, null=False)       # updated (was 160)
    family = models.ForeignKey(LocationFamily, on_delete=models.CASCADE,blank=False, null=False)
    # updated (was FK)
    type = models.ForeignKey(LocationType, on_delete=models.CASCADE, null=True, blank=True)
      # updated (was FK)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=False, null=False,related_name='locations')
            # updated (was FK)
    pavilion = models.CharField(max_length=120, null=True, blank=True)   # added
    room_no = models.CharField(max_length=40,blank=False, null=False)
    capacity = models.IntegerField(blank=True, null=True)
    building = models.ForeignKey('Building', models.DO_NOTHING,blank=False, null=False,related_name='locations')  # kept for compatibility
    
    class Meta:
        db_table = 'location'


# =========================
# REQUEST SETUP
# =========================

class RequestFamily(models.Model):
    request_family_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)

    class Meta:
        db_table = 'request_family'


class WorkFamily(models.Model):
    work_family_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)

    class Meta:
        db_table = 'work_family'


class Workflow(models.Model):
    workflow_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)

    class Meta:
        db_table = 'workflow'


class WorkflowStep(models.Model):
    step_id = models.BigAutoField(primary_key=True)
    workflow = models.ForeignKey('Workflow', models.DO_NOTHING)
    step_order = models.IntegerField()
    name = models.CharField(max_length=120,blank=False, null=False)
    role_hint = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = 'workflow_step'


class WorkflowTransition(models.Model):
    transition_id = models.BigAutoField(primary_key=True)
    from_step = models.ForeignKey('WorkflowStep', models.DO_NOTHING, related_name='transitions_from')
    to_step = models.ForeignKey('WorkflowStep', models.DO_NOTHING, related_name='transitions_to')
    condition_expr = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'workflow_transition'


class Checklist(models.Model):
    checklist_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100,blank=False, null=False)
    location = models.ForeignKey('Location',blank=False, null=False, on_delete=models.CASCADE)
    class Meta:
        db_table = 'checklist'


class ChecklistItem(models.Model):
    item_id = models.BigAutoField(primary_key=True)
    checklist = models.ForeignKey('Checklist', models.DO_NOTHING,blank=False, null=False)
    label = models.CharField(max_length=240, blank=True, null=True)
    required = models.BooleanField(default=False)

    class Meta:
        db_table = 'checklist_item'


class RequestType(models.Model):
    request_type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    workflow = models.ForeignKey('Workflow', models.DO_NOTHING,blank=False, null=False)
    work_family = models.ForeignKey('WorkFamily', models.DO_NOTHING,blank=False, null=False)
    request_family = models.ForeignKey('RequestFamily', models.DO_NOTHING,blank=False, null=False)
    checklist = models.ForeignKey('Checklist', models.DO_NOTHING,blank=False, null=False)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'request_type'


# =========================
# SERVICE REQUESTS
# =========================

class ServiceRequest(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    request_type = models.ForeignKey('RequestType', models.DO_NOTHING,blank=False, null=False)
    location = models.ForeignKey('Location', models.DO_NOTHING,blank=False, null=False)
    requester_user = models.ForeignKey('Users', models.DO_NOTHING, related_name='requests_made',blank=False, null=False)
    assignee_user = models.ForeignKey('Users', models.DO_NOTHING, related_name='requests_assigned',blank=False, null=False)
    priority = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'service_request'


class ServiceRequestStep(models.Model):
    request = models.ForeignKey('ServiceRequest', models.DO_NOTHING)
    step = models.ForeignKey('WorkflowStep', models.DO_NOTHING)
    status = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    actor_user = models.ForeignKey('Users', models.DO_NOTHING,blank=False, null=False)

    class Meta:
        db_table = 'service_request_step'
        unique_together = (('request', 'step'),)


class ServiceRequestChecklist(models.Model):
    request = models.ForeignKey('ServiceRequest', models.DO_NOTHING)
    item = models.ForeignKey('ChecklistItem', models.DO_NOTHING)
    completed = models.BooleanField(default=False)
    completed_by_user = models.ForeignKey('Users', models.DO_NOTHING,blank=False, null=False)

    class Meta:
        db_table = 'service_request_checklist'
        unique_together = (('request', 'item'),)


# =========================
# GUEST & COMMENTS
# =========================

class Guest(models.Model):
    guest_id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=160,blank=False, null=False)
    phone = models.CharField(max_length=15,blank=False, null=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    room_no = models.CharField(max_length=10,blank=False, null=False) 
    class Meta:
        db_table = 'guest'


class GuestComment(models.Model):
    comment_id = models.BigAutoField(primary_key=True)
    guest = models.ForeignKey('Guest', models.DO_NOTHING)
    location = models.ForeignKey('Location', models.DO_NOTHING,blank=False, null=False)
    channel = models.CharField(max_length=20)
    source = models.CharField(max_length=20)
    rating = models.IntegerField(blank=False, null=False)
    comment_text = models.TextField()
    linked_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'guest_comment'

class Booking(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    room_number = models.CharField(max_length=10,blank=False, null=False)

    def __str__(self):
        return f"{self.guest.full_name} - {self.room_number}"

# =========================
# VOUCHERS
# =========================

# class Voucher(models.Model):  # updated
#     guest_name = models.CharField(max_length=100)
#     voucher_code = models.CharField(max_length=100)
#     expiry_date = models.DateField()
#     redeemed = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True) 

#     class Meta:
#         db_table = 'voucher'
# app1/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os
from django.utils.html import format_html
import string
import random
from datetime import timedelta, date, datetime
from django.db import models, IntegrityError, transaction
from django.utils import timezone
import uuid
import os
from django.utils.html import format_html

def random_code(prefix="BKT", length=6):
    chars = string.ascii_uppercase + string.digits
    return prefix + ''.join(random.choices(chars, k=length))
def qr_upload_path(instance, filename):
    return os.path.join("qrcodes", filename)

class Voucher(models.Model):
    # keep id as default 'id' (you previously had id)
    voucher_code = models.CharField(max_length=100, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100,blank=False, null=False)
    phone_number = models.CharField(max_length=15,blank=False, null=False) 
    room_no = models.CharField(max_length=100,blank=False, null=False)   # added
    check_in_date = models.DateField(blank=True, null=True)            # added
    check_out_date = models.DateField(blank=True, null=True)           # added
    expiry_date = models.DateField(blank=True, null=True)              # existing-ish field (keep)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(blank=True, null=True)
    qr_code = models.CharField(max_length=400, blank=True, null=True)  # url / content
    qr_code_image = models.ImageField(upload_to=qr_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    adults = models.IntegerField(default=1,blank=False, null=False)   
    kids = models.IntegerField(default=0,blank=False, null=False) 
    is_used = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)
    qr_sent_whatsapp = models.BooleanField(default=False)
    scan_count = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0) 
    valid_dates = models.JSONField(default=list)       # e.g. ["2025-09-07", "2025-09-08"]
    scan_history = models.JSONField(default=list,blank=True)      
    include_breakfast = models.BooleanField(default=False)
    class Meta:
        db_table = "voucher"
    
    # def save(self, *args, **kwargs):
       
    #     # ✅ Always update quantity before saving
    #     self.quantity = (self.adults or 0) + (self.kids or 0)
        
        
    #     super().save(*args, **kwargs)

    # def is_valid_now(self):
    #     today = timezone.localdate()
    #     # valid if within stay dates or expiry_date
    #     if self.check_in_date and self.check_out_date:
    #         return self.check_in_date <= today <= self.check_out_date
    #     if self.expiry_date:
    #         return today <= self.expiry_date
    #     return True

    # def mark_redeemed(self, user=None):
    #     self.redeemed = True
    #     self.redeemed_at = timezone.now()
    #     self.save(update_fields=["redeemed", "redeemed_at"])
    # def __str__(self):
    #     return f"{self.voucher_code} - {self.guest_name}"

    # def is_used_display(self):
    #     if self.is_used:
    #         return format_html('<span style="color:red; font-weight:bold;">Expired</span>')
    #     return format_html('<span style="color:green; font-weight:bold;">Active</span>')
    # is_used_display.short_description = "Voucher Status"
    
     

    def _generate_unique_code(self, prefix="BF"):
        # tries a few times and returns a code
        for _ in range(10):
            code = random_code(prefix=prefix, length=6)
            # quick existence check to avoid a save attempt when already used
            if not Voucher.objects.filter(voucher_code=code).exists():
                return code
        # fallback to UUID if unlucky
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        self.quantity = (self.adults or 0) + (self.kids or 0)
        if self.valid_dates is None:
            self.valid_dates = []
        if self.scan_history is None:
            self.scan_history = []

        # Auto-generate valid_dates (check-in → check-out inclusive)
        if self.check_in_date and self.check_out_date and not self.valid_dates:
            dates = []
            current = self.check_in_date
            while current <= self.check_out_date:
                dates.append(current.isoformat())
                current += timedelta(days=1)
            self.valid_dates = dates

        if not self.voucher_code:
            self.voucher_code = self._generate_unique_code()

        super().save(*args, **kwargs)

    # -------------------------------
    # VALIDATION RULES
    # -------------------------------
    def is_expired(self):
    
     if not self.check_out_date:
        return False

     expiry_dt = datetime.combine(self.check_out_date, time(23, 59))

    # Make sure expiry_dt is timezone-aware
     if timezone.is_naive(expiry_dt):
        expiry_dt = timezone.make_aware(expiry_dt, timezone.get_current_timezone())

     return timezone.now() > expiry_dt


    def is_valid_today(self):
    
     today = timezone.localdate().isoformat()

    # 1. Not valid if expired
     if self.is_expired():
        return False

    # 2. Only one scan per day
     if today in (self.scan_history or []):
        return False

    # 3. Date must be in valid_dates
     if today not in (self.valid_dates or []):
        return False

    # 4. Special rule for breakfast
     if self.include_breakfast:
        now = timezone.localtime().time()
        if self.check_in_date and date.today() == self.check_in_date:
            # Must check-in before 10:30 AM if breakfast included
            if now > time(10, 30):
                return False  # missed breakfast window

    # ✅ Otherwise, valid
     return True


    def mark_scanned_today(self):
        """Mark today's scan if valid"""
        if self.is_valid_today():
            today = date.today().isoformat()
            if today not in (self.scan_history or []):
                self.scan_history = list(self.scan_history or [])
                self.scan_history.append(today)
                self.save(update_fields=["scan_history"])
                return True
        return False

    def is_used_display(self):
        if self.is_expired():
            return format_html('<span style="color:red;font-weight:bold;">Expired</span>')
        return format_html('<span style="color:green;font-weight:bold;">Active</span>')

    is_used_display.short_description = "Voucher Status"

class RedemptionLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name="redemption_logs")
    scanned_at = models.DateTimeField(auto_now_add=True)
    # scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # staff
    scanner_ip = models.CharField(max_length=60, blank=True, null=True)
    success = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True, null=True)
    

    class Meta:
        db_table = "redemption_log"
        ordering = ["-scanned_at"]


# Keep old BreakfastVoucher separately if needed, else remove


# =========================
# REVIEWS
# =========================

class Review(models.Model):  # added
    guest_name = models.CharField(max_length=100,blank=False, null=False)
    rating = models.IntegerField()
    feedback = models.TextField()

    class Meta:
        db_table = 'review'


# =========================
# GYM
# =========================

# class GymMember(models.Model):
#     member_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=100,blank=False, null=False)
#     phone = models.CharField(max_length=15,blank=False, null=False)
#     email = models.CharField(max_length=100, blank=True, null=True)
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     status = models.CharField(max_length=50, blank=True, null=True)
#     plan_type = models.CharField(max_length=50, blank=True, null=True)

#     class Meta:
#         db_table = 'gym_member'


# class GymVisitor(models.Model):
#     visitor_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=100,blank=False, null=False)
#     phone = models.CharField(max_length=15, blank=False, null=False)
#     email = models.CharField(max_length=100, blank=True, null=True)
#     registered_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'gym_visitor'


# class GymVisit(models.Model):
#     visit_id = models.BigAutoField(primary_key=True)
#     member = models.ForeignKey('GymMember', models.DO_NOTHING,blank=False, null=False)
#     visitor = models.ForeignKey('GymVisitor', models.DO_NOTHING,blank=False, null=False)
#     visit_at = models.DateTimeField(blank=False, null=False)
#     checked_by_user = models.ForeignKey('Users', models.DO_NOTHING,blank=False, null=False)
#     notes = models.CharField(max_length=240, blank=True, null=True)

#     class Meta:
#         db_table = 'gym_visit'

from django.db import models
from django.contrib.auth.models import User
import io, base64, qrcode
# =========================
# GYM MEMBER
# =========================
class GymMember(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]
    member_id = models.BigAutoField(primary_key=True)
    customer_code = models.CharField(max_length=50, unique=True, blank=False, null=False)  # like FGS0001
    full_name = models.CharField(max_length=100, blank=False, null=False)
    nik = models.CharField(max_length=20, blank=True, null=True)  # national ID
    address = models.CharField(max_length=255, blank=False, null=False)
    city = models.CharField(max_length=100, blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)  # Male/Female
    occupation = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=False, null=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=128, blank=False, null=False)
    qr_code = models.TextField(blank=True, null=True)  # store QR data
    qr_code_image = models.ImageField(upload_to="qr_codes/", null=True, blank=True)  # base64 or image path
    confirm_password = models.CharField(max_length=128, blank=False, null=False)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    plan_type = models.CharField(max_length=50, blank=True, null=True)
    qr_expired = models.BooleanField(default=False) 

    created_at = models.DateTimeField(auto_now_add=True)
       # Manual entry if needed
    expiry_date = models.DateField(blank=True, null=True)  # Auto 3 months validity
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 

    

    # Scan tracking
    scan_count = models.IntegerField(default=0)
    scan_history = models.JSONField(default=list, blank=True)

    

    class Meta:
        db_table = 'gym_member'

    def __str__(self):
        return f"{self.customer_code} - {self.full_name}"
    
    
    def is_expired(self):
        if not self.expiry_date:
            return False
        expiry_dt = datetime.combine(self.expiry_date, time(23, 59))
        if timezone.is_naive(expiry_dt):
            expiry_dt = timezone.make_aware(expiry_dt, timezone.get_current_timezone())
        return timezone.now() > expiry_dt

    from datetime import date, datetime

    def is_valid_today(self, max_scans_per_day=3):
        today = date.today().isoformat()
        if self.is_expired():
            return False
    
    # Count today's scans (assuming scan_history stores timestamps as ISO strings)
        today_scans = [scan for scan in (self.scan_history or []) if scan.startswith(today)]
        if len(today_scans) >= max_scans_per_day:
             return False
    
    # Must be between start_date and expiry_date
        if self.start_date and self.expiry_date:
            return self.start_date <= date.today() <= self.expiry_date
        return True


    from datetime import datetime, date

    def mark_scanned_today(self, max_scans_per_day=3):
        if not self.is_valid_today(max_scans_per_day=max_scans_per_day):
            return False
    
    # Ensure scan_history is a list
        self.scan_history = list(self.scan_history or [])
    
    # Store full timestamp instead of just date
        self.scan_history.append(datetime.now().isoformat())
        self.scan_count = (self.scan_count or 0) + 1
        self.save(update_fields=["scan_history", "scan_count"])
        return True


    def status_display(self):
        if self.is_expired():
            return format_html('<span style="color:red;font-weight:bold;">Expired</span>')
        return format_html('<span style="color:green;font-weight:bold;">Active</span>')


# =========================
# GYM VISITOR (non-member)
# =========================
class GymVisitor(models.Model):
    visitor_id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=100, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=False, null=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gym_visitor'

    def __str__(self):
        return self.full_name


# =========================
# GYM VISIT (log entry)
# =========================
class GymVisit(models.Model):
    visit_id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey('GymMember', models.DO_NOTHING, blank=True, null=True)
    visitor = models.ForeignKey('GymVisitor', models.DO_NOTHING, blank=True, null=True)
    visit_at = models.DateTimeField(auto_now_add=True)
    checked_by_user = models.ForeignKey(User, models.DO_NOTHING, blank=False, null=False)
    notes = models.CharField(max_length=240, blank=True, null=True)

    class Meta:
        db_table = 'gym_visit'

    def __str__(self):
        return f"Visit {self.visit_id} - {self.visit_at}"

# =========================
# COMPLAINTS
# =========================
from django.contrib.auth.models import User
# class Complaint(models.Model):
#     STATUS_CHOICES = [
#         ("NEW", "New"),
#         ("ACCEPTED", "Accepted"),
#         ("ON_HOLD", "On Hold"),
#         ("CLOSED", "Closed"),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE,blank=False, null=False)  # complaint filed by a user
#     category = models.CharField(max_length=100)
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     location = models.CharField(max_length=50,blank=False, null=False)

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
#     owner = models.CharField(max_length=100,blank=False, null=False)
#     created_on = models.DateTimeField(auto_now_add=True)
#     due_date = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = "complaint"

#     def __str__(self):
#         return f"{self.title} ({self.get_status_display()})"

class Complaint(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ASSIGNED", "Assigned"),
        ("ACCEPTED", "Accepted"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("ESCALATED", "Escalated"),
        ("REJECTED", "Rejected"),
        ("CLOSED", "Closed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    assigned_to    = models.ForeignKey(User, related_name="assigned_member", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    created_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    sla_start = models.DateTimeField(null=True, blank=True)
    sla_end = models.DateTimeField(null=True, blank=True)
    picture = models.ImageField(upload_to='complaint_photos/', null=True, blank=True)

    class Meta:
        db_table = 'complaint'

    def __str__(self):
        return f"{self.title} ({self.status})"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'notification'

    def __str__(self):
        return f"Notification to {self.recipient.username}"


# from django.db import models



# class Department(models.Model):
#     department_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'department'


# class UserGroup(models.Model):
#     group_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'user_group'


# class Users(models.Model):
#     user_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=160)
#     email = models.CharField(max_length=160, blank=True, null=True)
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     title = models.CharField(max_length=120, blank=True, null=True)
#     department = models.ForeignKey('Department', models.DO_NOTHING, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'users'


# class UserProfile(models.Model):
#     user = models.OneToOneField('Users', models.DO_NOTHING, primary_key=True)
#     avatar_url = models.CharField(max_length=255, blank=True, null=True)
#     timezone = models.CharField(max_length=100, blank=True, null=True)
#     preferences = models.JSONField(blank=True, null=True)

#     class Meta:
#         db_table = 'user_profile'


# class UserGroupMembership(models.Model):
#     user = models.ForeignKey('Users', models.DO_NOTHING)
#     group = models.ForeignKey('UserGroup', models.DO_NOTHING)
#     joined_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'user_group_membership'
#         unique_together = (('user', 'group'),)


# # =========================
# # LOCATIONS
# # =========================

# class Building(models.Model):
#     building_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'building'


# class Floor(models.Model):
#     floor_id = models.BigAutoField(primary_key=True)
#     building = models.ForeignKey('Building', models.DO_NOTHING)
#     floor_number = models.IntegerField()

#     class Meta:
#         db_table = 'floor'


# class LocationFamily(models.Model):
#     family_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'location_family'


# class LocationType(models.Model):
#     type_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'location_type'


# class Location(models.Model):
#     location_id = models.BigAutoField(primary_key=True)
#     family = models.ForeignKey('LocationFamily', models.DO_NOTHING, blank=True, null=True)
#     type = models.ForeignKey('LocationType', models.DO_NOTHING, blank=True, null=True)
#     building = models.ForeignKey('Building', models.DO_NOTHING, blank=True, null=True)
#     floor = models.ForeignKey('Floor', models.DO_NOTHING, blank=True, null=True)
#     name = models.CharField(max_length=160)
#     room_no = models.CharField(max_length=40, blank=True, null=True)
#     capacity = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'location'


# # =========================
# # REQUEST SETUP
# # =========================

# class RequestFamily(models.Model):
#     request_family_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'request_family'


# class WorkFamily(models.Model):
#     work_family_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'work_family'


# class Workflow(models.Model):
#     workflow_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=120)

#     class Meta:
#         db_table = 'workflow'


# class WorkflowStep(models.Model):
#     step_id = models.BigAutoField(primary_key=True)
#     workflow = models.ForeignKey('Workflow', models.DO_NOTHING)
#     step_order = models.IntegerField()
#     name = models.CharField(max_length=120)
#     role_hint = models.CharField(max_length=120, blank=True, null=True)

#     class Meta:
#         db_table = 'workflow_step'


# class WorkflowTransition(models.Model):
#     transition_id = models.BigAutoField(primary_key=True)
#     from_step = models.ForeignKey('WorkflowStep', models.DO_NOTHING, related_name='transitions_from')
#     to_step = models.ForeignKey('WorkflowStep', models.DO_NOTHING, related_name='transitions_to')
#     condition_expr = models.JSONField(blank=True, null=True)

#     class Meta:
#         db_table = 'workflow_transition'


# class Checklist(models.Model):
#     checklist_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=100)

#     class Meta:
#         db_table = 'checklist'


# class ChecklistItem(models.Model):
#     item_id = models.BigAutoField(primary_key=True)
#     checklist = models.ForeignKey('Checklist', models.DO_NOTHING)
#     label = models.CharField(max_length=240, blank=True, null=True)
#     required = models.BooleanField(default=False)

#     class Meta:
#         db_table = 'checklist_item'


# class RequestType(models.Model):
#     request_type_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=100)
#     workflow = models.ForeignKey('Workflow', models.DO_NOTHING, blank=True, null=True)
#     work_family = models.ForeignKey('WorkFamily', models.DO_NOTHING, blank=True, null=True)
#     request_family = models.ForeignKey('RequestFamily', models.DO_NOTHING, blank=True, null=True)
#     checklist = models.ForeignKey('Checklist', models.DO_NOTHING, blank=True, null=True)
#     active = models.BooleanField(default=True)

#     class Meta:
#         db_table = 'request_type'


# # =========================
# # SERVICE REQUESTS
# # =========================

# class ServiceRequest(models.Model):
#     request_id = models.BigAutoField(primary_key=True)
#     request_type = models.ForeignKey('RequestType', models.DO_NOTHING, blank=True, null=True)
#     location = models.ForeignKey('Location', models.DO_NOTHING, blank=True, null=True)
#     requester_user = models.ForeignKey('Users', models.DO_NOTHING, related_name='requests_made', blank=True, null=True)
#     assignee_user = models.ForeignKey('Users', models.DO_NOTHING, related_name='requests_assigned', blank=True, null=True)
#     priority = models.CharField(max_length=20, blank=True, null=True)
#     status = models.CharField(max_length=50, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     closed_at = models.DateTimeField(blank=True, null=True)
#     notes = models.TextField(blank=True, null=True)

#     class Meta:
#         db_table = 'service_request'


# class ServiceRequestStep(models.Model):
#     request = models.ForeignKey('ServiceRequest', models.DO_NOTHING)
#     step = models.ForeignKey('WorkflowStep', models.DO_NOTHING)
#     status = models.CharField(max_length=20, blank=True, null=True)
#     started_at = models.DateTimeField(blank=True, null=True)
#     completed_at = models.DateTimeField(blank=True, null=True)
#     actor_user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

#     class Meta:
#         db_table = 'service_request_step'
#         unique_together = (('request', 'step'),)


# class ServiceRequestChecklist(models.Model):
#     request = models.ForeignKey('ServiceRequest', models.DO_NOTHING)
#     item = models.ForeignKey('ChecklistItem', models.DO_NOTHING)
#     completed = models.BooleanField(default=False)
#     completed_by_user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

#     class Meta:
#         db_table = 'service_request_checklist'
#         unique_together = (('request', 'item'),)


# # =========================
# # GUEST & COMMENTS
# # =========================

# class Guest(models.Model):
#     guest_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=160, blank=True, null=True)
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     email = models.CharField(max_length=100, blank=True, null=True)

#     class Meta:
#         db_table = 'guest'


# class GuestComment(models.Model):
#     comment_id = models.BigAutoField(primary_key=True)
#     guest = models.ForeignKey('Guest', models.DO_NOTHING)
#     location = models.ForeignKey('Location', models.DO_NOTHING, blank=True, null=True)
#     channel = models.CharField(max_length=20)
#     source = models.CharField(max_length=20)
#     rating = models.IntegerField(blank=True, null=True)
#     comment_text = models.TextField()
#     linked_flag = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'guest_comment'


# # =========================
# # VOUCHERS
# # =========================

# class BreakfastVoucher(models.Model):
#     voucher_id = models.BigAutoField(primary_key=True)
#     guest = models.ForeignKey('Guest', models.DO_NOTHING, blank=True, null=True)
#     customer_name = models.CharField(max_length=160, blank=True, null=True)
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     email = models.CharField(max_length=100, blank=True, null=True)
#     room_no = models.CharField(max_length=20, blank=True, null=True)
#     location = models.ForeignKey('Location', models.DO_NOTHING, blank=True, null=True)
#     qr_code = models.CharField(max_length=255, blank=True, null=True)
#     qr_code_image = models.CharField(max_length=255, blank=True, null=True)
#     adults = models.IntegerField(default=1)   
#     kids = models.IntegerField(default=0)  
#     qty = models.IntegerField()
#     status = models.CharField(max_length=20, blank=True, null=True)
#     sent_whatsapp = models.BooleanField(default=False)
#     sent_at = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'breakfast_voucher'


# class BreakfastVoucherScan(models.Model):
#     scan_id = models.BigAutoField(primary_key=True)
#     voucher = models.ForeignKey('BreakfastVoucher', models.DO_NOTHING)
#     scanned_at = models.DateTimeField(auto_now_add=True)
#     source = models.CharField(max_length=20, blank=True, null=True)
#     scanned_by_user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

#     class Meta:
#         db_table = 'breakfast_voucher_scan'


# # =========================
# # GYM
# # =========================

# class GymMember(models.Model):
#     member_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=15)
#     email = models.CharField(max_length=100, blank=True, null=True)
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     status = models.CharField(max_length=50, blank=True, null=True)
#     plan_type = models.CharField(max_length=50, blank=True, null=True)

#     class Meta:
#         db_table = 'gym_member'


# class GymVisitor(models.Model):
#     visitor_id = models.BigAutoField(primary_key=True)
#     full_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     email = models.CharField(max_length=100, blank=True, null=True)
#     registered_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'gym_visitor'


# class GymVisit(models.Model):
#     visit_id = models.BigAutoField(primary_key=True)
#     member = models.ForeignKey('GymMember', models.DO_NOTHING, blank=True, null=True)
#     visitor = models.ForeignKey('GymVisitor', models.DO_NOTHING, blank=True, null=True)
#     visit_at = models.DateTimeField(blank=True, null=True)
#     checked_by_user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
#     notes = models.CharField(max_length=240, blank=True, null=True)

#     class Meta:
#         db_table = 'gym_visit'

# from django.contrib.auth.models import User

# class Complaint(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     category = models.CharField(max_length=100)
#     description = models.TextField()
#     status = models.CharField(max_length=50, default='Pending')

#     class Meta:
#         db_table= 'complaint'



# complaints/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Complaint, Notification
from datetime import timedelta
from django.contrib.auth.models import User

@shared_task
def send_notification(user_id, message):
    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)
    Notification.objects.create(recipient=user, message=message)

@shared_task
def check_sla():
    now = timezone.now()
    overdue = Complaint.objects.filter(
        status__in=["ASSIGNED", "ACCEPTED", "IN_PROGRESS"],
        sla_start__isnull=False,
        sla_end__isnull=True          # Only running SLAs
    )
    for c in overdue:
        if now > c.sla_start + timedelta(hours=4):
            c.status = "ESCALATED"
            c.save()
            if c.department and c.department.lead:
                send_notification.delay(
                    c.department.lead.id,
                    f"Complaint {c.id} has been escalated (SLA exceeded)."
                )

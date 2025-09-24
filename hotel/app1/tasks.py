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
    """Run every 5 minutes to escalate overdue complaints"""
    now = timezone.now()
    overdue_complaints = Complaint.objects.filter(status__in=["ASSIGNED", "ACCEPTED", "IN_PROGRESS"], sla_start__isnull=False)
    for c in overdue_complaints:
        sla_limit = c.sla_start + timedelta(hours=4)  # Example: 4 hours SLA
        if now > sla_limit:
            c.status = "ESCALATED"
            c.save()
            # Notify manager or lead
            if c.department:
                leads = User.objects.filter(is_staff=True, department=c.department)
                for lead in leads:
                    send_notification.delay(lead.id, f"Complaint {c.id} has been escalated.")

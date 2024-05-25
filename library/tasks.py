from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from library.models import Reservation, Borrow
from django.utils import timezone


@shared_task
def cancel_expired_reservations():
    now = timezone.now()
    expired_reservations = Reservation.objects.filter(expires_at__lte=now, is_active=True)
    count = expired_reservations.update(is_active=False)
    return count


@shared_task
def send_overdue_notifications():
    now = timezone.now()
    overdue_borrows = Borrow.objects.filter(due_date__lte=now, returned_at__isnull=True)
    for borrow in overdue_borrows:
        send_mail(
            'Overdue Book Notification',
            f'Dear {borrow.user.first_name}, the book "{borrow.book.title}" you borrowed is overdue. Please return it '
            f'as soon as possible.',
            settings.DEFAULT_FROM_EMAIL,
            [borrow.user.email],
        )

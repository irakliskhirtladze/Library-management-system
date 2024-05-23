from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Reservation


class Command(BaseCommand):
    help = 'Cancels expired reservations'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_reservations = Reservation.objects.filter(expires_at__lte=now, is_active=True)

        count = expired_reservations.update(is_active=False)

        self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {count} expired reservations'))

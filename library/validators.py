from django.core.exceptions import ValidationError


def validate_no_active_reservation(user, book=None, ignore_instance=None):
    """Validates that the user does not have an active reservation"""
    from library.models import Reservation

    active_reservations = Reservation.objects.filter(user=user, is_active=True)
    if ignore_instance:
        active_reservations = active_reservations.exclude(pk=ignore_instance.pk)
    if active_reservations.exists():
        if book and not active_reservations.filter(book=book).exists():
            raise ValidationError("This user has an active reservation for a different book.")
        raise ValidationError("This user already has an active reservation.")


def validate_no_active_borrowing(user, ignore_instance=None):
    """Validates that the user does not have an unreturned borrowing."""
    from library.models import Borrow

    active_borrowings = Borrow.objects.filter(user=user, returned_at__isnull=True)
    if ignore_instance:
        active_borrowings = active_borrowings.exclude(pk=ignore_instance.pk)
    if active_borrowings.exists():
        raise ValidationError("This user already has an active borrowing.")

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone


class Author(models.Model):
    """
    Model representing an author.
    """
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Genre(models.Model):
    """
    Model representing a genre.
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Model representing a book.
    """
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    release_year = models.IntegerField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.title


class Reservation(models.Model):
    """
    Model representing a reservation.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(hours=24))
    is_active = models.BooleanField(default=True)

    def clean(self):
        """
        Validate that the user does not have an unreturned borrowing before saving the reservation.
        """
        if Borrow.objects.filter(user=self.user, returned_at__isnull=True).exists():
            raise ValidationError("This user has an unreturned borrowing and cannot make a reservation.")

        # Ensure only one active reservation per user
        if self.is_active and Reservation.objects.filter(user=self.user, is_active=True).exists():
            raise ValidationError("This user already has an active reservation.")

    def save(self, *args, **kwargs):
        try:
            self.clean()
            super().save(*args, **kwargs)
        except ValidationError as e:
            raise e

    def __str__(self):
        return f'{self.user.email} reserved {self.book.title}'


class Borrow(models.Model):
    """
    Model representing a borrowing.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=14))
    returned_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        """
        Validate that the user does not have another active borrowing or an active reservation for a different book.
        """
        if self.returned_at is None:  # Only check for active borrowings if this is not a return
            if Borrow.objects.filter(user=self.user, returned_at__isnull=True).exists():
                raise ValidationError("This user already has an active borrowing.")

            active_reservations = Reservation.objects.filter(user=self.user, is_active=True)
            if active_reservations.exists() and not active_reservations.filter(book=self.book).exists():
                raise ValidationError("This user has an active reservation for a different book.")

    def save(self, *args, **kwargs):
        try:
            self.clean()
            super().save(*args, **kwargs)
        except ValidationError as e:
            raise e

    def __str__(self):
        return f'{self.user.email} borrowed {self.book.title}'

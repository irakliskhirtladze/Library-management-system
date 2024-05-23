from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from library.validators import validate_no_active_borrowing, validate_no_active_reservation, validate_book_availability


class Author(models.Model):
    """
    Model representing an author.
    """
    full_name = models.CharField(max_length=100, verbose_name=_('Full Name'))

    class Meta:
        verbose_name = _('Author')
        verbose_name_plural = _('Authors')

    def __str__(self):
        return self.full_name


class Genre(models.Model):
    """
    Model representing a genre.
    """
    name = models.CharField(max_length=100, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Model representing a book.
    """
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name=_('Author'))
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name=_('Genre'))
    wished_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='wished_books', blank=True)
    title = models.CharField(max_length=100, verbose_name=_('Title'))
    release_year = models.IntegerField(verbose_name=_('Release Year'))
    quantity = models.IntegerField(verbose_name=_('Quantity'))

    @property
    def currently_borrowed_count(self):
        return Borrow.objects.filter(book=self, returned_at__isnull=True).count()

    @property
    def active_reservations_count(self):
        return Reservation.objects.filter(book=self, is_active=True).count()

    @property
    def total_borrowed_count(self):
        return Borrow.objects.filter(book=self).count()

    @property
    def available_copies(self):
        return self.quantity - (self.currently_borrowed_count + self.active_reservations_count)

    @property
    def is_available(self):
        return self.available_copies > 0

    def notify_wishers(self):
        """Send a notification to all wishers of the book when it becomes available."""
        if self.is_available:
            for user in self.wished_by.all():
                send_mail(
                    'Book Available Notification',
                    f'Dear {user.email},\n\n'
                    f'The book "{self.title}" is now available. You can reserve or borrow it.\n\n'
                    'Thank you.',
                    'from@example.com',  # Replace with your sender email
                    [user.email],
                    fail_silently=False,
                )
            self.wished_by.clear()

    def borrow_history(self):
        return Borrow.objects.filter(book=self).select_related('user').order_by('-borrowed_at')

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    def __str__(self):
        return self.title


class Reservation(models.Model):
    """
    Model representing a reservation.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('User'))
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name=_('Book'))
    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Reserved At'))
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(hours=24),
                                      verbose_name=_('Expires At'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))

    def clean(self):
        """
        Validate that the user does not have an unreturned borrowing before saving the reservation.
        Plus, validate that only one active reservation per user is allowed.
        """
        validate_book_availability(self.book)
        validate_no_active_borrowing(self.user, ignore_instance=self)
        validate_no_active_reservation(self.user, ignore_instance=self)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.clean()
        super().save(*args, **kwargs)
        # Notify the book's wishers (if they exist) when reservation is canceled
        if not self.is_active and not is_new:
            self.book.notify_wishers()

    class Meta:
        verbose_name = _('Reservation')
        verbose_name_plural = _('Reservations')

    def __str__(self):
        return f'{self.user.email} reserved {self.book.title}'


class Borrow(models.Model):
    """
    Model representing a borrowing.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('User'))
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name=_('Book'))
    borrowed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Borrowed At'))
    due_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=14), verbose_name=_('Due Date'))
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Returned At'))

    def clean(self):
        """
        Validate that the user does not have another active borrowing or an active reservation for a different book.
        """
        if self.returned_at is None:
            validate_book_availability(self.book)
            validate_no_active_borrowing(self.user, ignore_instance=self)

            # Check if the user has an active reservation for a different book
            active_reservations = Reservation.objects.filter(user=self.user, is_active=True)
            if active_reservations.exists() and not active_reservations.filter(book=self.book).exists():
                raise ValidationError("This user has an active reservation for a different book.")

    def save(self, *args, **kwargs):
        """Cancel the reservation if the user borrows the reserved book."""
        is_new = self.pk is None
        self.clean()
        super().save(*args, **kwargs)
        # Notify the book's wishers (if they exist) when borrowed book is returned
        if self.returned_at and not is_new:
            self.book.notify_wishers()
        Reservation.objects.filter(user=self.user, book=self.book, is_active=True).update(is_active=False)

    class Meta:
        verbose_name = _('Borrow')
        verbose_name_plural = _('Borrows')

    def __str__(self):
        return f'{self.user.email} borrowed {self.book.title}'

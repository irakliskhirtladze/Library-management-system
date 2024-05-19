from django.db import models
from django.conf import settings
from django.utils import timezone


class Author(models.Model):
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    release_year = models.IntegerField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.title


class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(hours=24))
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Ensure only one active reservation per user
        if self.is_active and Reservation.objects.filter(user=self.user, is_active=True).exists():
            raise ValueError("This user already has an active reservation.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.email} reserved {self.book.title}'


class Borrow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=14))
    returned_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Ensure that a user with an active reservation can only borrow the reserved book
        active_reservations = Reservation.objects.filter(user=self.user, is_active=True)
        if active_reservations.exists():
            if not active_reservations.filter(book=self.book).exists():
                raise ValueError(
                    "You cannot borrow another book while you have an active reservation for a different book.")
            else:
                active_reservation = active_reservations.filter(book=self.book).first()
                active_reservation.is_active = False
                active_reservation.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.email} borrowed {self.book.title}'

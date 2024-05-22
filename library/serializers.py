from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import serializers

from library.models import Author, Genre, Book, Reservation, Borrow
from library.validators import validate_no_active_borrowing, validate_no_active_reservation

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for Author model.
    """
    class Meta:
        model = Author
        fields = ['id', 'full_name']


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for Genre model.
    """
    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for Book model.
    """
    author = AuthorSerializer()
    genre = GenreSerializer()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'release_year', 'quantity', 'currently_borrowed_count',
                  'active_reservations_count', 'total_borrowed_count']


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for Reservation model.
    Ensures that only one active reservation per user is allowed.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'book', 'reserved_at', 'expires_at']

    def __init__(self, *args, **kwargs):
        """
        Set default user to the user field for non-staff users and remove this field from the serializer input.
        Plus, remove the expires_at field from the serializer input.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request and not request.user.is_staff:
            self.fields['user'].read_only = True
            self.fields['user'].default = request.user
            self.fields.pop('user')

        self.fields.pop('expires_at')


class BorrowSerializer(serializers.ModelSerializer):
    """
    Serializer for Borrow model.
    Ensures that only one active borrowing per user is allowed.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    due_date = serializers.DateTimeField(default=timezone.now() + timezone.timedelta(days=14))

    class Meta:
        model = Borrow
        fields = ['id', 'user', 'book', 'borrowed_at', 'due_date', 'returned_at']

    def __init__(self, *args, **kwargs):
        """
        Remove the due_date field from the serializer input
        """
        super().__init__(*args, **kwargs)
        self.fields.pop('due_date')

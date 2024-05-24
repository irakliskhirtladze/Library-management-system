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


class BorrowHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for Borrow history.
    """
    user = serializers.StringRelatedField()

    class Meta:
        model = Borrow
        fields = ['user', 'borrowed_at', 'returned_at']


class BookListSerializer(serializers.ModelSerializer):
    """
    Serializer for Book model.
    """
    author = AuthorSerializer()
    genre = GenreSerializer()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'release_year']


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

    def add_wish(self, user):
        """
        Add a wish for the book.
        """
        if self.instance.is_available:
            raise serializers.ValidationError("This book is currently available and cannot be wished for.")
        self.instance.wished_by.add(user)
        self.instance.save()
        return self.instance

    def remove_wish(self, user):
        """
        Remove a wish for the book.
        """
        self.instance.wished_by.remove(user)
        self.instance.save()
        return self.instance


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for Reservation model. Only book field is required.
    """
    class Meta:
        model = Reservation
        fields = ['id']

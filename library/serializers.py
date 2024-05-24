from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import serializers

from library.models import Author, Genre, Book, Reservation, Borrow
from library.validators import validate_no_active_borrowing, validate_no_active_reservation

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']


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
                  'active_reservations_count', 'total_borrowed_count', 'borrow_count_last_year']


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for Reservation model. Only book field is required.
    """
    class Meta:
        model = Reservation
        fields = ['id']


class BorrowSerializer(serializers.ModelSerializer):
    """
    Serializer for Borrow model
    """
    user = serializers.StringRelatedField()

    class Meta:
        model = Borrow
        fields = ['user', 'borrowed_at', 'returned_at']


class EmptySerializer(serializers.Serializer):
    """Empty serializer to be used for wish endpoints"""
    pass

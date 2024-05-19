from django.utils import timezone
from rest_framework import serializers
from library.models import Author, Genre, Book, Reservation, Borrow
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'full_name']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    genre = GenreSerializer()
    borrowed_count = serializers.SerializerMethodField()
    reservations_count = serializers.SerializerMethodField()
    total_borrowed_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'release_year', 'quantity', 'borrowed_count', 'reservations_count',
                  'total_borrowed_count']

    def get_borrowed_count(self, obj):
        return Borrow.objects.filter(book=obj, returned_at__isnull=True).count()

    def get_reservations_count(self, obj):
        return Reservation.objects.filter(book=obj, is_active=True).count()

    def get_total_borrowed_count(self, obj):
        return Borrow.objects.filter(book=obj).count()


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'book', 'reserved_at', 'expires_at']

    def validate(self, data):
        user = data['user']
        if Reservation.objects.filter(user=user, is_active=True).exists():
            raise serializers.ValidationError("You cannot make another reservation while you have an active one.")
        return data

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class BorrowSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Borrow
        fields = ['id', 'user', 'book', 'borrowed_at', 'due_date', 'returned_at']

    def validate(self, data):
        user = data['user']
        book = data['book']
        active_reservations = Reservation.objects.filter(user=user, is_active=True)
        if active_reservations.exists():
            if not active_reservations.filter(book=book).exists():
                raise serializers.ValidationError("You cannot borrow another book while you have "
                                                  "an active reservation for a different book.")
        return data

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

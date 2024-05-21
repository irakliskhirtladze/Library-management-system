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
        Initialize the serializer and customize the user field for non-staff users.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request and not request.user.is_staff:
            self.fields['user'].read_only = True
            self.fields['user'].default = request.user

        # Remove the expires_at field from the serializer input
        self.fields.pop('expires_at')

    def validate(self, data):
        """
        Validate that there are no active reservations or unreturned borrowings for the user.
        """
        request = self.context.get('request', None)
        if request and not request.user.is_staff:
            data['user'] = request.user
        user = data['user']

        validate_no_active_borrowing(user)
        validate_no_active_reservation(user)

        # # Check for active reservations
        # if Reservation.objects.filter(user=user, is_active=True).exists():
        #     raise serializers.ValidationError("You cannot make another reservation while having an active one.")
        #
        # # Check for unreturned borrowings
        # if Borrow.objects.filter(user=user, returned_at__isnull=True).exists():
        #     raise serializers.ValidationError("You cannot make a reservation while having an unreturned borrowing.")

        return data

    def create(self, validated_data):
        """
        Create a new reservation instance.
        """
        request = self.context.get('request', None)
        if request and not request.user.is_staff:
            validated_data['user'] = request.user

        # # Set the default expires_at if it's not provided
        # if 'expires_at' not in validated_data:
        #     validated_data['expires_at'] = timezone.now() + timezone.timedelta(hours=24)

        try:
            return super().create(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        """
        Customize the representation of the reservation instance.
        Remove the user field for non-staff users.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        # if request:
        #     representation.pop('due_date')
        if request and not request.user.is_staff:
            representation.pop('user')
        return representation


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

    def validate(self, data):
        """
        Validate that there are no active borrowings or unreturned borrowings for the user.
        """
        user = data['user']
        book = data['book']

        validate_no_active_borrowing(user)
        validate_no_active_reservation(user, book)

        # if 'returned_at' not in self.initial_data:
        #     # Check for active borrowings
        #     if Borrow.objects.filter(user=user, returned_at__isnull=True).exists():
        #         raise serializers.ValidationError("You cannot borrow another book while you have an active borrowing.")
        #
        #     # Check for active reservations
        #     active_reservations = Reservation.objects.filter(user=user, is_active=True)
        #     if active_reservations.exists() and not active_reservations.filter(book=book).exists():
        #         raise serializers.ValidationError("You cannot borrow another book while you have "
        #                                           "an active reservation for a different book.")
        return data

    def create(self, validated_data):
        """
        Create a new borrowing instance.
        """
        # Set the default due_date if it's not provided
        if 'due_date' not in validated_data:
            validated_data['due_date'] = timezone.now() + timezone.timedelta(days=14)

        try:
            return super().create(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        """
        Update the borrowing instance.
        """
        try:
            return super().update(instance, validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

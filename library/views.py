from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status, permissions, filters
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from library.permissions import IsLibrarian
from users.models import CustomUser
from users.serializers import CustomUserSerializer
from library.models import Author, Genre, Book, Reservation, Borrow
from library.serializers import AuthorSerializer, GenreSerializer, BookSerializer, ReservationSerializer, \
    BorrowSerializer, BorrowHistorySerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing authors.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get_permissions(self):
        """
        Assign permissions based on action.
        Only admin users can list or retrieve authors.
        Only admin users can create, update, or delete authors.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]


class GenreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing genres.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def get_permissions(self):
        """
        Assign permissions based on action.
        Only admin users can list or retrieve genres.
        Only admin users can create, update, or delete genres.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books.
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genre']
    search_fields = ['title', 'author__full_name', 'genre__name']
    ordering_fields = ['title', 'release_year', 'popularity']

    def get_permissions(self):
        """
        Assign permissions based on action.
        All authenticated users can list or retrieve books.
        Only admin users can create, update, or delete books.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Customize the queryset to include popularity annotation.
        """
        queryset = super().get_queryset()
        queryset = queryset.annotate(popularity=Count('borrow'))
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[IsLibrarian])
    def borrow_history(self, request, pk=None):
        """
        Custom action to retrieve the borrow history of a book.
        """
        book = self.get_object()
        borrows = Borrow.objects.filter(book=book).select_related('user').order_by('-borrowed_at')
        serializer = BorrowHistorySerializer(borrows, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def wish(self, request, pk=None):
        """
        Custom action to make a wish for an unavailable book.
        """
        book = self.get_object()
        user = request.user

        serializer = self.get_serializer(book)
        try:
            serializer.add_wish(user)
            return Response(
                {"detail": "Your wish has been recorded. You will be notified when the book becomes available."},
                status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_wish(self, request, pk=None):
        """
        Custom action to remove a wish for a book.
        """
        book = self.get_object()
        user = request.user

        serializer = self.get_serializer(book)
        serializer.remove_wish(user)
        return Response({"detail": "Your wish has been removed."}, status=status.HTTP_200_OK)


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reservations.
    """
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'book__title']

    def get_permissions(self):
        """
        Assign permissions based on action.
        All authenticated users can create or cancel reservations.
        Only admins can create, update, partially update, or delete reservations for other users.
        """
        if self.action in ['create', 'cancel']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsLibrarian]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Customize the queryset to filter based on the user.
        """
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.all()
        else:
            return Reservation.objects.filter(user=user, is_active=True)

    def perform_create(self, serializer):
        """
        Save the reservation instance, ensuring the user is correctly chosen if librarian is making the reservation.
        """
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Override the create method to handle validation errors and return them as API responses.
        """
        try:
            return super().create(request, *args, **kwargs)
        # Check if it's a ValidationError and has a message_dict attribute
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise DRFValidationError(e.message_dict)
            else:
                raise DRFValidationError(e.messages)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Custom action to cancel a reservation.
        """
        reservation = self.get_object()
        if reservation.user != request.user and not request.user.is_staff:
            return Response({"detail": "You do not have permission to cancel this reservation."},
                            status=status.HTTP_403_FORBIDDEN)
        reservation.is_active = False
        reservation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BorrowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing borrowings.
    """
    queryset = Borrow.objects.all()
    serializer_class = BorrowSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'book__title']

    def get_permissions(self):
        """
        Assign permissions based on action.
        All authenticated users can list or retrieve borrowings.
        Only admins can create, update, partially update, or delete borrowings.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'return_book']:
            permission_classes = [IsLibrarian]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Customize the queryset to filter based on the user.
        """
        user = self.request.user
        if user.is_staff:
            return Borrow.objects.all()
        else:
            return Borrow.objects.filter(user=user, returned_at__isnull=True)

    def perform_create(self, serializer):
        """
        Save the borrowing instance, ensuring the user field is correctly set.
        """
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def create(self, request, *args, **kwargs):
        """
        Override the create method to handle validation errors and return them as API responses.
        """
        try:
            return super().create(request, *args, **kwargs)
        except DjangoValidationError as e:
            # Check if it's a ValidationError and has a message_dict attribute
            if hasattr(e, 'message_dict'):
                raise DRFValidationError(e.message_dict)
            else:
                raise DRFValidationError(e.messages)

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        """
        Custom action to borrow a book.
        """
        book = self.get_object()
        user = request.user

        try:
            due_date = timezone.now() + timezone.timedelta(days=14)
            borrow = Borrow.objects.create(user=user, book=book, due_date=due_date)
            serializer = self.get_serializer(borrow)
            return Response(serializer.data)
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise DRFValidationError(e.message_dict)
            else:
                raise DRFValidationError(e.messages)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """
        Custom action to return a book.
        """
        borrow = self.get_object()
        borrow.returned_at = timezone.now()
        borrow.save()
        serializer = self.get_serializer(borrow)
        return Response(serializer.data)


class PopularBooksView(APIView):
    """
    API view to get 10 most popular books based on borrow count.
    """
    def get(self, request):
        books = Book.objects.annotate(borrow_count=Count('borrow')).order_by('-borrow_count')[:10]
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class BorrowCountLastYearView(APIView):
    """
    API view to get the borrow count for each book in the last year.
    """
    def get(self, request):
        one_year_ago = timezone.now() - timezone.timedelta(days=365)
        books = Book.objects.annotate(borrow_count=Count('borrow', filter=Q(borrow__borrowed_at__gte=one_year_ago)))
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class LateReturnsView(APIView):
    """
    API view to get the list of top 100 late returned books.
    """
    def get(self, request):
        late_borrows = Borrow.objects.filter(returned_at__gt=F('due_date')).order_by('-returned_at')[:100]
        serializer = BorrowSerializer(late_borrows, many=True)
        return Response(serializer.data)


class LateReturningUsersView(APIView):
    """
    API view to get the list of top 100 users who returned books late.
    """
    def get(self, request):
        late_returns = Borrow.objects.filter(returned_at__gt=F('due_date')).values('user').\
                           annotate(late_count=Count('id')).order_by('-late_count')[:100]
        user_ids = [entry['user'] for entry in late_returns]
        users = CustomUser.objects.filter(id__in=user_ids)
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)

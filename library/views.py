from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from library.permissions import IsLibrarian
from library.models import Author, Genre, Book, Reservation, Borrow
from library.serializers import AuthorSerializer, GenreSerializer, BookSerializer, ReservationSerializer, \
    BookListSerializer, EmptySerializer, BorrowSerializer, CustomUserSerializer
from users.models import CustomUser


class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing authors.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get_permissions(self):
        """
        Assign permissions based on action.
        Only admin users can create, update, or delete authors.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
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
        Only admin users can create, update, or delete genres.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing books, reservations and wishes for unavailable books.
    """
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genre']
    search_fields = ['title', 'author__full_name', 'genre__name']
    ordering_fields = ['id', 'popularity']

    def get_permissions(self):
        """
        Assign permissions based on action.
        """
        if self.action in ['borrow_history', 'create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsLibrarian]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Customize the queryset to include popularity annotation.
        """
        queryset = super().get_queryset()
        queryset = queryset.annotate(popularity=Count('borrow'))
        return queryset

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['reserve', 'cancel_reservation']:
            return ReservationSerializer
        elif self.action in ['wish', 'remove_wish']:
            return EmptySerializer
        return BookSerializer

    @action(detail=True, methods=['get'], permission_classes=[IsLibrarian])
    def borrow_history(self, request, pk=None):
        """
        Custom action to retrieve the borrow history of a book.
        """
        book = self.get_object()
        borrows = Borrow.objects.filter(book=book).select_related('user').order_by('-borrowed_at')
        serializer = BorrowSerializer(borrows, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reserve(self, request, pk=None):
        """
        Custom action to reserve a book.
        """
        book = self.get_object()
        user = request.user

        try:
            reservation = Reservation.objects.create(user=user, book=book)
            serializer = ReservationSerializer(reservation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            # Handle both message_dict and messages attributes
            if hasattr(e, 'message_dict'):
                return Response({"detail": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel_reservation(self, request, pk=None):
        """
        Custom action to cancel a reservation for a book.
        """
        try:
            reservation = Reservation.objects.get(book_id=pk, user=request.user, is_active=True)
            reservation.is_active = False
            reservation.save()
            return Response({"detail": "Reservation canceled successfully."}, status=status.HTTP_200_OK)
        except Reservation.DoesNotExist:
            return Response({"detail": "Active reservation not found for this book."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def wish(self, request, pk=None):
        """
        Custom action to make a wish for an unavailable book.
        """
        book = self.get_object()
        user = request.user

        if book.is_available:
            return Response({"detail": "This book is currently available and cannot make a wish for it."},
                            status=status.HTTP_400_BAD_REQUEST)

        book.wished_by.add(user)
        return Response(
            {"detail": "Your wish has been recorded. You will be notified when the book becomes available."},
            status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_wish(self, request, pk=None):
        """
        Custom action to remove a wish for a book.
        """
        book = self.get_object()
        user = request.user

        if not book.wished_by.filter(id=user.id).exists():
            return Response({"detail": "You have not wished for this book, so it cannot be removed."},
                            status=status.HTTP_400_BAD_REQUEST)

        book.wished_by.remove(user)
        return Response({"detail": "Your wish for this book has been removed."}, status=status.HTTP_200_OK)


class StatisticsViewSet(viewsets.ViewSet):
    """
    ViewSet for library statistics.
    """

    @action(detail=False, methods=['get'])
    def popular_books(self, request):
        """
        Custom action to get 10 most popular books based on borrow count.
        """
        books = Book.objects.annotate(borrow_count=Count('borrow')).order_by('-borrow_count')[:10]
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def late_returns(self, request):
        """
        Custom action to get the list of top 100 late returned books.
        """
        late_borrows = Borrow.objects.filter(returned_at__gt=F('due_date')).order_by('-returned_at')[:100]
        serializer = BorrowSerializer(late_borrows, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def late_returning_users(self, request):
        """
        Custom action to get the list of top 100 users who returned books late.
        """
        late_returns = Borrow.objects.filter(returned_at__gt=F('due_date')).values('user'). \
            annotate(late_count=Count('id')).order_by('-late_count')[:100]
        user_ids = [entry['user'] for entry in late_returns]
        users = CustomUser.objects.filter(id__in=user_ids)
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)

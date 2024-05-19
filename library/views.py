from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status, permissions, filters
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from library.permissions import IsLibrarian
from users.models import CustomUser
from users.serializers import CustomUserSerializer
from library.models import Author, Genre, Book, Reservation, Borrow
from library.serializers import AuthorSerializer, GenreSerializer, BookSerializer, ReservationSerializer,\
    BorrowSerializer


def home(request):
    return render(request, 'index.html')


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAdminUser]  # Normal users shouldn't access Authors
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAdminUser]  # Normal users shouldn't access Genres
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genre']  # Add fields to filter by
    search_fields = ['title', 'author__full_name', 'genre__name']  # Add fields to search by
    ordering_fields = ['title', 'release_year', 'popularity']  # Add fields to sort by

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsLibrarian]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Count the number of times the book has been borrowed
        queryset = queryset.annotate(popularity=Count('borrow'))
        return queryset


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'book__title']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsLibrarian]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BorrowViewSet(viewsets.ModelViewSet):
    queryset = Borrow.objects.all()
    serializer_class = BorrowSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'book__title']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsLibrarian]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        book = self.get_object()
        user = request.user
        if Borrow.objects.filter(user=user, returned_at__isnull=True).exists():
            return Response({"detail": "You cannot borrow another book while you have an active borrowing."},
                            status=status.HTTP_400_BAD_REQUEST)
        due_date = timezone.now() + timezone.timedelta(days=14)
        borrow = Borrow.objects.create(user=user, book=book, due_date=due_date)
        book.quantity -= 1
        book.save()
        serializer = self.get_serializer(borrow)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        borrow = self.get_object()
        borrow.returned_at = timezone.now()
        borrow.save()
        borrow.book.quantity += 1
        borrow.book.save()
        serializer = self.get_serializer(borrow)
        return Response(serializer.data)


class PopularBooksView(APIView):
    def get(self, request):
        books = Book.objects.annotate(borrow_count=Count('borrow')).order_by('-borrow_count')[:10]
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class BorrowCountLastYearView(APIView):
    def get(self, request):
        one_year_ago = timezone.now() - timezone.timedelta(days=365)
        books = Book.objects.annotate(borrow_count=Count('borrow', filter=Q(borrow__borrowed_at__gte=one_year_ago)))
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class LateReturnsView(APIView):
    def get(self, request):
        late_borrows = Borrow.objects.filter(returned_at__gt=F('due_date')).order_by('-returned_at')[:100]
        serializer = BorrowSerializer(late_borrows, many=True)
        return Response(serializer.data)


class LateReturningUsersView(APIView):
    def get(self, request):
        late_returns = Borrow.objects.filter(returned_at__gt=F('due_date')).values('user').annotate(late_count=Count('id')).order_by('-late_count')[:100]
        user_ids = [entry['user'] for entry in late_returns]
        users = CustomUser.objects.filter(id__in=user_ids)
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)

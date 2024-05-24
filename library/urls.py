from django.urls import path
from rest_framework.routers import DefaultRouter
from library.views import AuthorViewSet, GenreViewSet, BookViewSet,\
    PopularBooksView, BorrowCountLastYearView, LateReturnsView, LateReturningUsersView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'books', BookViewSet, basename='book')
# router.register(r'reservations', ReservationViewSet, basename='reservation')
# router.register(r'borrows', BorrowViewSet, basename='borrow')

urlpatterns = router.urls

urlpatterns += [
    path('statistics/popular-books/', PopularBooksView.as_view(), name='popular_books'),
    path('statistics/borrow-count-last-year/', BorrowCountLastYearView.as_view(), name='borrow_count_last_year'),
    path('statistics/late-returns/', LateReturnsView.as_view(), name='late_returns'),
    path('statistics/late-returning-users/', LateReturningUsersView.as_view(), name='late_returning_users'),
]

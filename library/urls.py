from django.urls import path
from rest_framework.routers import DefaultRouter
from library.views import AuthorViewSet, GenreViewSet, BookViewSet, StatisticsViewSet, user_book_status

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'books', BookViewSet, basename='book')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

urlpatterns = router.urls

urlpatterns += [
    path('user_book_status/<int:pk>/', user_book_status, name='user_book_status'),
]

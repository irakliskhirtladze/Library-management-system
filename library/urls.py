from django.urls import path
from rest_framework.routers import DefaultRouter
from library.views import AuthorViewSet, GenreViewSet, BookViewSet, StatisticsViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'books', BookViewSet, basename='book')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

urlpatterns = router.urls

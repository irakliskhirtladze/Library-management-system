from django.urls import path

from web.views import home, book_detail

urlpatterns = [
    path('', home, name='home'),
    path('books/<int:pk>/', book_detail, name='book_detail'),
]

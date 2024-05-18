from django.contrib import admin
from .models import Author, Genre, Book, Reservation, Borrow


class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name']
    search_fields = ['full_name']


class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'release_year', 'quantity']
    search_fields = ['title', 'author__full_name', 'genre__name']
    list_filter = ['genre', 'author']
    ordering = ['title']


class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'reserved_at', 'expires_at']
    search_fields = ['user__email', 'book__title']
    list_filter = ['reserved_at', 'expires_at']


class BorrowAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'borrowed_at', 'due_date', 'returned_at']
    search_fields = ['user__email', 'book__title']
    list_filter = ['borrowed_at', 'due_date', 'returned_at']


admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Borrow, BorrowAdmin)

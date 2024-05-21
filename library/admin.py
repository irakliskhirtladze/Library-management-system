from django.contrib import admin
from django import forms

from library.models import Author, Genre, Book, Reservation, Borrow


class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name']
    search_fields = ['full_name']


class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class ReservationAdminForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['user', 'book', 'expires_at', 'is_active']


class BorrowAdminForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['user', 'book', 'due_date', 'returned_at']


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'release_year', 'quantity', 'currently_borrowed_count',
                    'active_reservations_count', 'total_borrowed_count']
    readonly_fields = ('currently_borrowed_count', 'active_reservations_count', 'total_borrowed_count')
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'genre', 'release_year', 'quantity')
        }),
        ('Additional Information', {
            'fields': ('currently_borrowed_count', 'active_reservations_count', 'total_borrowed_count')
        }),
    )
    search_fields = ['title', 'author__full_name', 'genre__name']
    list_filter = ['genre', 'author']
    ordering = ['title']


class ReservationAdmin(admin.ModelAdmin):
    form = ReservationAdminForm
    list_display = ['user', 'book', 'reserved_at', 'expires_at', 'is_active']
    search_fields = ['user__email', 'book__title']
    list_filter = ['reserved_at', 'expires_at']


class BorrowAdmin(admin.ModelAdmin):
    form = BorrowAdminForm
    list_display = ['user', 'book', 'borrowed_at', 'due_date', 'returned_at']
    search_fields = ['user__email', 'book__title']
    list_filter = ['borrowed_at', 'due_date', 'returned_at']


admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Borrow, BorrowAdmin)

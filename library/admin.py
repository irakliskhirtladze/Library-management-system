from django.contrib import admin
from django import forms
from django.shortcuts import render
from django.utils.html import format_html
from django.urls import reverse, path

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
                    'active_reservations_count', 'total_borrowed_count', 'borrow_history_link']
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

    def borrow_history_link(self, obj):
        """
        Returns a link to the borrow history for the given book.
        """
        url = reverse('admin:borrow_history', args=[obj.pk])
        return format_html('<a href="{}">View History</a>', url)

    borrow_history_link.short_description = 'Borrow History'

    def get_urls(self):
        """
        Add custom URL for borrow history view.
        """
        urls = super().get_urls()
        custom_urls = [
            path('borrow-history/<int:book_id>/', self.admin_site.admin_view(self.borrow_history_view),
                 name='borrow_history'),
        ]
        return custom_urls + urls

    def borrow_history_view(self, request, book_id):
        """
        Custom view to display the borrow history of a book.
        """
        book = Book.objects.get(pk=book_id)
        borrows = book.borrow_history()
        context = dict(
            self.admin_site.each_context(request),
            book=book,
            borrows=borrows,
        )
        return render(request, 'admin/borrow_history.html', context)


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

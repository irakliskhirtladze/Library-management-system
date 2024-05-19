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

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        if Reservation.objects.filter(user=user, is_active=True).exists():
            raise forms.ValidationError("This user already has an active reservation.")
        return cleaned_data


class BorrowAdminForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['user', 'book', 'due_date', 'returned_at']

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        book = cleaned_data.get("book")
        active_reservations = Reservation.objects.filter(user=user, is_active=True)
        if active_reservations.exists():
            if not active_reservations.filter(book=book).exists():
                raise forms.ValidationError("This user cannot borrow another book while "
                                            "having an active reservation for a different book.")
        return cleaned_data


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'release_year', 'quantity', 'borrowed_count', 'reservations_count',
                    'total_borrowed_count']
    readonly_fields = ('borrowed_count', 'reservations_count', 'total_borrowed_count')
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'genre', 'release_year', 'quantity')
        }),
        ('Additional Information', {
            'fields': ('borrowed_count', 'reservations_count', 'total_borrowed_count')
        }),
    )
    search_fields = ['title', 'author__full_name', 'genre__name']
    list_filter = ['genre', 'author']
    ordering = ['title']

    def borrowed_count(self, obj):
        return Borrow.objects.filter(book=obj, returned_at__isnull=True).count()
    borrowed_count.short_description = 'Currently Borrowed Count'

    def reservations_count(self, obj):
        return Reservation.objects.filter(book=obj, is_active=True).count()
    reservations_count.short_description = 'Active Reservations Count'

    def total_borrowed_count(self, obj):
        return Borrow.objects.filter(book=obj).count()
    total_borrowed_count.short_description = 'Total Times Borrowed'


class ReservationAdmin(admin.ModelAdmin):
    form = ReservationAdminForm
    list_display = ['user', 'book', 'reserved_at', 'expires_at', 'is_active']
    search_fields = ['user__email', 'book__title']
    list_filter = ['reserved_at', 'expires_at']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_staff:
            form.base_fields['user'].widget = forms.HiddenInput()
            form.base_fields['user'].initial = request.user
        return form


class BorrowAdmin(admin.ModelAdmin):
    form = BorrowAdminForm
    list_display = ['user', 'book', 'borrowed_at', 'due_date', 'returned_at']
    search_fields = ['user__email', 'book__title']
    list_filter = ['borrowed_at', 'due_date', 'returned_at']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_staff:
            form.base_fields['user'].widget = forms.HiddenInput()
            form.base_fields['user'].initial = request.user
        return form


admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Borrow, BorrowAdmin)

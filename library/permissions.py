from rest_framework import permissions


class IsLibrarian(permissions.BasePermission):
    """Custom permission to only allow librarians to create, update, and delete objects."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

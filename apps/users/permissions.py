from rest_framework import permissions


class IsHimselfOrAdmin(permissions.BasePermission):
    """
    Check if user is accessing information of himself, or if user is a staff
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff

from rest_framework.permissions import BasePermission


class IsDispatcher(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "DISPATCHER"
        )
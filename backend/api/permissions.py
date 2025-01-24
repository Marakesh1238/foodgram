from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class IsAuthenticatedOr401(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed(
                'Authentication credentials were not provided.'
            )
        return True

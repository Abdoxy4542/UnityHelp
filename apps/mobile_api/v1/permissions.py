from rest_framework import permissions
from rest_framework.authtoken.models import Token


class IsMobileUser(permissions.BasePermission):
    """
    Custom permission to only allow mobile authenticated users
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Read permissions for any mobile user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner or admin
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == 'admin'

        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.role == 'admin'

        if hasattr(obj, 'respondent'):
            return obj.respondent == request.user or request.user.role == 'admin'

        return request.user.role == 'admin'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        if hasattr(obj, 'respondent'):
            return obj.respondent == request.user

        return False


class IsGSOOrAdmin(permissions.BasePermission):
    """
    Permission for GSO (Gathering Site Official) or Admin users only
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['gso', 'admin']
        )


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission for verified users only
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )


class CanCreateSites(permissions.BasePermission):
    """
    Permission for users who can create sites
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Allow read for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow create/update for GSO, admin, and certain NGO users
        return request.user.role in ['gso', 'admin', 'ngo_user']


class CanSubmitAssessments(permissions.BasePermission):
    """
    Permission for users who can submit assessments
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # All authenticated users can read
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only verified users can submit assessments
        return request.user.is_verified


class RoleBasedPermission(permissions.BasePermission):
    """
    Role-based permission system
    """

    def __init__(self, allowed_roles=None, allow_self=True):
        self.allowed_roles = allowed_roles or []
        self.allow_self = allow_self

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin always has access
        if request.user.role == 'admin':
            return True

        # Check if user's role is in allowed roles
        if self.allowed_roles and request.user.role in self.allowed_roles:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin always has access
        if request.user.role == 'admin':
            return True

        # Allow access if user owns the object
        if self.allow_self:
            if hasattr(obj, 'user') and obj.user == request.user:
                return True
            if hasattr(obj, 'created_by') and obj.created_by == request.user:
                return True
            if hasattr(obj, 'respondent') and obj.respondent == request.user:
                return True

        # Check role-based access
        if self.allowed_roles and request.user.role in self.allowed_roles:
            return True

        return False
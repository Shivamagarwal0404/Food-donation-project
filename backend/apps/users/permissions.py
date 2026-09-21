"""
FoodShare — User permission classes.
Role-based access control for Donors, NGOs, Volunteers, and Platform Admins.
"""
from rest_framework import permissions
from .models import UserRole


def is_admin_or_staff(user):
    """
    Unified check for platform administrator or staff status.
    Covers is_staff, is_superuser, is_admin_user, and role == UserRole.ADMIN.
    """
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "is_admin_user", False)
            or getattr(user, "role", None) == UserRole.ADMIN
        )
    )


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to platform admins and superusers."""

    message = "Only platform administrators can perform this action."

    def has_permission(self, request, view):
        return is_admin_or_staff(request.user)


class IsDonor(permissions.BasePermission):
    """Allows access to food donors and platform admins."""

    message = "Only registered food donors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_donor or is_admin_or_staff(request.user))
        )


class IsNGOReceiver(permissions.BasePermission):
    """Allows access to NGO receivers and platform admins."""

    message = "Only registered NGO receivers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_ngo or is_admin_or_staff(request.user))
        )


class IsVerifiedNGO(permissions.BasePermission):
    """Allows access only to verified NGOs and platform admins."""

    message = "Only verified NGOs can perform this action. Administrator verification is required."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if is_admin_or_staff(request.user):
            return True
        if request.user.is_ngo:
            ngo_profile = getattr(request.user, "ngo_profile", None)
            return bool(ngo_profile and ngo_profile.is_verified)
        return False


class IsVolunteer(permissions.BasePermission):
    """Allows access to delivery volunteers and platform admins."""

    message = "Only registered volunteers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_volunteer or is_admin_or_staff(request.user))
        )



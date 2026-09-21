"""
FoodShare — Custom UserManager.
Handles creation of regular users and superusers using email as the primary identifier.
"""
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for custom User model with email authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower().strip()
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        if "phone_number" in extra_fields:
            if extra_fields["phone_number"]:
                extra_fields["phone_number"] = str(extra_fields["phone_number"]).strip()
            else:
                extra_fields["phone_number"] = None
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


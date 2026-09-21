"""
FoodShare — Users & Profiles models.

Defines:
- UserRole: ADMIN, DONOR, NGO_RECEIVER, VOLUNTEER
- User: Email-based authentication with role-based permissions
- DonorProfile: Extended information for food donors
- NGOProfile: Extended information for recipient organizations (NGOs, shelters, food banks)
- VolunteerProfile: Extended information for logistics and delivery volunteers
- Address: Saved addresses for pickup, delivery, and headquarters
"""
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from .managers import UserManager


class UserRole(models.TextChoices):
    ADMIN = "admin", _("Platform Admin")
    DONOR = "donor", _("Food Donor")
    NGO_RECEIVER = "ngo_receiver", _("NGO / Community Receiver")
    VOLUNTEER = "volunteer", _("Delivery Volunteer")


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom user model using email as username.
    Passwords are encrypted with PBKDF2/SHA256 via Django's set_password().
    """

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.DONOR,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(_("verified"), default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("email"),
                name="unique_lower_email",
            ),
            models.UniqueConstraint(
                fields=["phone_number"],
                name="unique_non_empty_phone_number",
                condition=models.Q(phone_number__isnull=False) & ~models.Q(phone_number=""),
            ),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_donor(self):
        return self.role == UserRole.DONOR

    @property
    def is_ngo(self):
        return self.role == UserRole.NGO_RECEIVER

    @property
    def is_volunteer(self):
        return self.role == UserRole.VOLUNTEER

    @property
    def is_admin_user(self):
        return self.role == UserRole.ADMIN


class DonorProfile(TimeStampedModel):
    """Profile for donors: restaurants, bakeries, supermarkets, catering, individuals."""

    class DonorType(models.TextChoices):
        INDIVIDUAL = "individual", _("Individual / Household")
        RESTAURANT = "restaurant", _("Restaurant / Cafe")
        HOTEL = "hotel", _("Hotel / Banquet")
        SUPERMARKET = "supermarket", _("Supermarket / Grocery")
        BAKERY = "bakery", _("Bakery")
        CATERER = "caterer", _("Catering Service")
        CORPORATE = "corporate", _("Corporate Cafeteria")
        OTHER = "other", _("Other")

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="donor_profile",
    )
    donor_type = models.CharField(
        max_length=30,
        choices=DonorType.choices,
        default=DonorType.RESTAURANT,
    )
    organization_name = models.CharField(max_length=255, blank=True)
    fssai_license = models.CharField(
        _("FSSAI / Food License Number"),
        max_length=50,
        blank=True,
    )

    def __str__(self):
        return f"Donor: {self.organization_name or self.user.full_name}"


class NGOProfile(TimeStampedModel):
    """Profile for recipient NGOs, charity kitchens, shelters, and orphanages."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ngo_profile",
    )
    organization_name = models.CharField(max_length=255)
    registration_number = models.CharField(
        _("NGO Registration / 12A / 80G Number"),
        max_length=100,
        blank=True,
    )
    mission_statement = models.TextField(blank=True)
    capacity_servings_per_day = models.PositiveIntegerField(
        _("Capacity (meals served/day)"),
        default=50,
    )
    is_verified = models.BooleanField(
        _("Verification Status"),
        default=False,
        help_text=_("Designates whether this NGO has been verified by platform administrators."),
    )

    def __str__(self):
        return f"NGO: {self.organization_name} (Verified: {self.is_verified})"


class VolunteerProfile(TimeStampedModel):
    """Profile for delivery and pickup volunteers."""

    class VehicleType(models.TextChoices):
        WALK = "walk", _("On Foot")
        BICYCLE = "bicycle", _("Bicycle")
        TWO_WHEELER = "two_wheeler", _("Motorcycle / Scooter")
        CAR = "car", _("Car")
        VAN = "van", _("Mini-Van / Cargo Van")

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    vehicle_type = models.CharField(
        max_length=30,
        choices=VehicleType.choices,
        default=VehicleType.TWO_WHEELER,
    )
    is_available = models.BooleanField(default=True)
    deliveries_completed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Volunteer: {self.user.full_name} ({self.get_vehicle_type_display()})"


class Address(TimeStampedModel):
    """
    Physical addresses for food pickup points, NGO facilities, and delivery locations.
    """

    class AddressType(models.TextChoices):
        PICKUP = "pickup", _("Donor Food Pickup Location")
        DELIVERY = "delivery", _("NGO Distribution Center / Shelter")
        OFFICE = "office", _("Office / Headquarters")
        HOME = "home", _("Home / Residence")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.PICKUP,
    )
    contact_person = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="India")
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return f"{self.contact_person} — {self.address_line1}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class EmailOTP(TimeStampedModel):
    """
    Stores single-use, hashed OTPs for email verification and password reset.
    Plaintext OTP is never stored in the database.
    """

    class OTPPurpose(models.TextChoices):
        REGISTRATION = "registration", _("Registration Verification")
        PASSWORD_RESET = "password_reset", _("Password Reset")
        LOGIN = "login", _("Login Verification")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_otps",
    )
    purpose = models.CharField(
        max_length=32,
        choices=OTPPurpose.choices,
        default=OTPPurpose.REGISTRATION,
    )
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    class Meta:
        verbose_name = _("email OTP")
        verbose_name_plural = _("email OTPs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "purpose", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"OTP ({self.purpose}) for {self.user.email} (Used: {self.is_used}, Expired: {self.is_expired()})"

    @classmethod
    def hash_otp(cls, user_id: int, code: str, purpose: str = OTPPurpose.REGISTRATION) -> str:
        secret_key = getattr(settings, "SECRET_KEY", "foodshare-otp-secret")
        if purpose == cls.OTPPurpose.LOGIN:
            salt = f"{secret_key}:{user_id}:login:otp"
        elif purpose == cls.OTPPurpose.PASSWORD_RESET:
            salt = f"{secret_key}:{user_id}:password_reset:otp"
        else:
            salt = f"{secret_key}:{user_id}:otp"
        return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()

    @classmethod
    def create_otp(cls, user, validity_minutes: int = 10, purpose: str = OTPPurpose.REGISTRATION):
        print(f"[FoodShare OTP] EmailOTP.create_otp ({purpose}) called for user: {user.email}")
        # Invalidate any existing unused OTPs for this user and this specific purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

        code = f"{secrets.randbelow(1000000):06d}"
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        otp = cls.objects.create(
            user=user,
            purpose=purpose,
            otp_hash=cls.hash_otp(user.id, code, purpose=purpose),
            expires_at=expires_at,
        )

        from django.core.mail import send_mail
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@foodshare.org")
        print(f"[FoodShare OTP] Calling send_mail ({purpose}) to {user.email} from {from_email}")
        if purpose == cls.OTPPurpose.LOGIN:
            subject = "FoodShare Login Verification Code"
            action_desc = "login verification"
        elif purpose == cls.OTPPurpose.PASSWORD_RESET:
            subject = "FoodShare Password Reset Code"
            action_desc = "password reset"
        else:
            subject = "FoodShare Email Verification Code"
            action_desc = "verification"

        send_mail(
            subject=subject,
            message=(
                f"Hello {user.first_name or 'User'},\n\n"
                f"Your FoodShare {action_desc} code is: {code}\n\n"
                f"This code will expire in {validity_minutes} minutes.\n\n"
                "If you did not request this, please ignore this email.\n\n"
                "Warm regards,\nFoodShare Team\n"
            ),
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print("[FoodShare OTP] send_mail executed successfully")

        return otp, code

    @classmethod
    def generate_otp(cls, user, validity_minutes: int = 10, purpose: str = OTPPurpose.REGISTRATION):
        return cls.create_otp(user, validity_minutes, purpose=purpose)

    def verify(self, code: str) -> bool:
        if self.is_used or self.is_expired():
            return False

        self.attempts += 1
        expected_hash = self.hash_otp(self.user.id, code, purpose=self.purpose)

        if self.attempts >= self.max_attempts:
            self.is_used = True
            self.save(update_fields=["attempts", "is_used"])
            return False

        if secrets.compare_digest(self.otp_hash, expected_hash):
            self.is_used = True
            self.save(update_fields=["attempts", "is_used"])
            return True

        self.save(update_fields=["attempts"])
        return False

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


"""
FoodShare — Donations models.

Defines:
- FoodCategory: Classification of food donations
- DonationStatus: Controlled lifecycle stages
- FoodDonation: Core food surplus donation record with validation
- DonationRequest: NGO claim request on a donation
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class FoodCategory(TimeStampedModel):
    """Categories of surplus food (e.g., Cooked Meals, Bakery, Produce)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text=_("UI icon name or emoji"))
    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this category is active and selectable for donations."),
    )

    class Meta:
        verbose_name = _("food category")
        verbose_name_plural = _("food categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class DonationStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("Available")
    REQUESTED = "REQUESTED", _("Requested by NGO")
    ACCEPTED = "ACCEPTED", _("Claim Accepted")
    PICKUP_ASSIGNED = "PICKUP_ASSIGNED", _("Pickup Assigned")
    PICKED_UP = "PICKED_UP", _("Picked Up")
    DELIVERED = "DELIVERED", _("Delivered to NGO")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    EXPIRED = "EXPIRED", _("Expired")


class DietaryType(models.TextChoices):
    VEG = "VEG", _("Vegetarian")
    NON_VEG = "NON_VEG", _("Non-Vegetarian")
    VEGAN = "VEGAN", _("Vegan")
    EGG = "EGG", _("Contains Egg")


class QuantityUnit(models.TextChoices):
    KG = "kg", _("Kilograms (kg)")
    MEALS = "meals", _("Meals / Servings")
    PACKETS = "packets", _("Packets / Boxes")
    LITERS = "liters", _("Liters (L)")


class FoodDonation(TimeStampedModel):
    """
    Core Food Donation entity posted by Donors.
    Tracks food item details, safe handling times, and lifecycle progress.
    """

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations",
    )
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.PROTECT,
        related_name="donations",
    )
    other_food_item = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Specific food item description when category is 'Other'."),
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dietary_type = models.CharField(
        max_length=20,
        choices=DietaryType.choices,
        default=DietaryType.VEG,
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(
        max_length=20,
        choices=QuantityUnit.choices,
        default=QuantityUnit.MEALS,
    )
    servings = models.PositiveIntegerField(
        help_text=_("Estimated number of people this donation can feed."),
        default=10,
    )
    prepared_at = models.DateTimeField(null=True, blank=True)
    expiry_at = models.DateTimeField(
        help_text=_("Food safety expiration deadline. Must be strictly respected."),
    )
    pickup_address = models.TextField(
        help_text=_("Full physical address where the food can be collected."),
    )
    pickup_city = models.CharField(max_length=100, default="Local")
    pickup_contact_phone = models.CharField(max_length=20)
    image = models.ImageField(
        upload_to="donations/",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=25,
        choices=DonationStatus.choices,
        default=DonationStatus.AVAILABLE,
    )
    special_instructions = models.TextField(
        blank=True,
        help_text=_("Storage requirements, refrigeration notes, container instructions."),
    )

    VALID_TRANSITIONS = {
        DonationStatus.AVAILABLE: [
            DonationStatus.REQUESTED,
            DonationStatus.ACCEPTED,
            DonationStatus.CANCELLED,
            DonationStatus.EXPIRED,
        ],
        DonationStatus.REQUESTED: [
            DonationStatus.ACCEPTED,
            DonationStatus.AVAILABLE,
            DonationStatus.CANCELLED,
            DonationStatus.EXPIRED,
        ],
        DonationStatus.ACCEPTED: [
            DonationStatus.PICKUP_ASSIGNED,
            DonationStatus.CANCELLED,
        ],
        DonationStatus.PICKUP_ASSIGNED: [
            DonationStatus.PICKED_UP,
            DonationStatus.CANCELLED,
        ],
        DonationStatus.PICKED_UP: [
            DonationStatus.DELIVERED,
        ],
        DonationStatus.DELIVERED: [
            DonationStatus.COMPLETED,
        ],
        DonationStatus.COMPLETED: [],
        DonationStatus.CANCELLED: [],
        DonationStatus.EXPIRED: [],
    }

    class Meta:
        verbose_name = _("food donation")
        verbose_name_plural = _("food donations")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["expiry_at"]),
            models.Index(fields=["donor"]),
            models.Index(fields=["pickup_city"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.quantity} {self.unit}) — {self.get_status_display()}"

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be strictly greater than 0."})
        if self.servings is not None and self.servings < 1:
            raise ValidationError({"servings": "Servings must be at least 1."})
        if self.expiry_at and self.expiry_at <= timezone.now() and self.status == DonationStatus.AVAILABLE:
            raise ValidationError({"expiry_at": "Expiry time must be in the future."})

    def can_transition_to(self, target_status):
        """Validates if transitioning to target_status is allowed by the lifecycle."""
        if self.status == target_status:
            return True
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        return target_status in allowed

    def transition_to(self, target_status, save=True):
        """Safely transitions status with lifecycle enforcement."""
        if not self.can_transition_to(target_status):
            raise ValidationError(
                f"Cannot transition donation '{self.title}' from {self.status} to {target_status}."
            )
        self.status = target_status
        if save:
            self.save(update_fields=["status", "updated_at"])

    @property
    def is_expired(self):
        return self.expiry_at <= timezone.now()


class DonationRequest(TimeStampedModel):
    """
    Claim request made by an NGO/Receiver to reserve an available food donation.
    """

    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending Donor Review")
        ACCEPTED = "ACCEPTED", _("Accepted")
        REJECTED = "REJECTED", _("Rejected")
        CANCELLED = "CANCELLED", _("Cancelled by NGO")

    donation = models.ForeignKey(
        FoodDonation,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donation_requests",
    )
    requested_servings = models.PositiveIntegerField(
        help_text=_("Number of servings requested for distribution."),
    )
    message = models.TextField(
        blank=True,
        help_text=_("Purpose / beneficiary details (e.g., homeless shelter, community meal)."),
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )

    class Meta:
        verbose_name = _("donation request")
        verbose_name_plural = _("donation requests")
        constraints = [
            models.UniqueConstraint(
                fields=["donation", "receiver"],
                condition=models.Q(status__in=["PENDING", "ACCEPTED"]),
                name="unique_active_request_per_receiver",
            )
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["receiver"]),
        ]

    def __str__(self):
        return f"Request by {self.receiver.full_name} for {self.donation.title} [{self.status}]"


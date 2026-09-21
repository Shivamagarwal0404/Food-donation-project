"""
FoodShare — Pickups models.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.donations.models import FoodDonation, DonationStatus


class PickupStatus(models.TextChoices):
    PENDING = "PENDING", _("Awaiting Volunteer Assignment")
    ASSIGNED = "ASSIGNED", _("Volunteer Assigned")
    PICKED_UP = "PICKED_UP", _("Food Picked Up")
    DELIVERED = "DELIVERED", _("Food Delivered to NGO")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class Pickup(TimeStampedModel):
    """
    Logistics tracking entity for collecting accepted food donations and delivering to the recipient NGO.
    """

    donation = models.OneToOneField(
        FoodDonation,
        on_delete=models.CASCADE,
        related_name="pickup",
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_pickups",
    )
    pickup_location = models.TextField()
    delivery_location = models.TextField(blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=25,
        choices=PickupStatus.choices,
        default=PickupStatus.PENDING,
    )
    notes = models.TextField(blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    VALID_TRANSITIONS = {
        PickupStatus.PENDING: [PickupStatus.ASSIGNED, PickupStatus.CANCELLED],
        PickupStatus.ASSIGNED: [
            PickupStatus.PICKED_UP,
            PickupStatus.CANCELLED,
        ],
        PickupStatus.PICKED_UP: [
            PickupStatus.DELIVERED,
        ],
        PickupStatus.DELIVERED: [
            PickupStatus.COMPLETED,
        ],
        PickupStatus.COMPLETED: [],
        PickupStatus.CANCELLED: [],
    }

    class Meta:
        verbose_name = _("pickup")
        verbose_name_plural = _("pickups")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["volunteer"]),
        ]

    def __str__(self):
        vol_name = self.volunteer.full_name if self.volunteer else "Unassigned"
        return f"Pickup for '{self.donation.title}' [{self.get_status_display()}] — {vol_name}"

    def transition_to(self, target_status):
        """Validate and execute state transition for Pickup entity."""
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        if target_status not in allowed:
            raise ValidationError(
                f"Invalid status transition from {self.status} to {target_status}."
            )
        self.status = target_status
        if target_status == PickupStatus.PICKED_UP and not self.picked_up_at:
            self.picked_up_at = timezone.now()
        elif target_status == PickupStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
        self.save(update_fields=["status", "picked_up_at", "delivered_at", "updated_at"])

    def assign_volunteer(self, volunteer):
        if self.status != PickupStatus.PENDING:
            raise ValidationError(f"Cannot assign volunteer to pickup with status {self.status}.")
        self.volunteer = volunteer
        self.save(update_fields=["volunteer", "updated_at"])
        self.transition_to(PickupStatus.ASSIGNED)
        if self.donation.status == DonationStatus.ACCEPTED:
            self.donation.transition_to(DonationStatus.PICKUP_ASSIGNED)

    def mark_picked_up(self):
        if self.status != PickupStatus.ASSIGNED:
            raise ValidationError(f"Cannot mark food picked up from status {self.status} (must be ASSIGNED).")
        self.transition_to(PickupStatus.PICKED_UP)
        if self.donation.status == DonationStatus.PICKUP_ASSIGNED:
            self.donation.transition_to(DonationStatus.PICKED_UP)

    def mark_delivered(self):
        if self.status != PickupStatus.PICKED_UP:
            raise ValidationError(f"Cannot mark food delivered from status {self.status} (must be PICKED_UP).")
        self.transition_to(PickupStatus.DELIVERED)
        if self.donation.status == DonationStatus.PICKED_UP:
            self.donation.transition_to(DonationStatus.DELIVERED)

    def mark_completed(self):
        if self.status != PickupStatus.DELIVERED:
            raise ValidationError(f"Cannot complete pickup from status {self.status} (must be DELIVERED).")
        self.transition_to(PickupStatus.COMPLETED)
        if self.donation.status == DonationStatus.DELIVERED:
            self.donation.transition_to(DonationStatus.COMPLETED)
        if self.volunteer and hasattr(self.volunteer, "volunteer_profile"):
            self.volunteer.volunteer_profile.deliveries_completed += 1
            self.volunteer.volunteer_profile.save(update_fields=["deliveries_completed"])

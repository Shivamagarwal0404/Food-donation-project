"""
FoodShare — Analytics views.
Provides transparent, calculation-backed community food rescue metrics.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Q

from apps.users.models import User, UserRole
from apps.donations.models import FoodDonation, DonationStatus


class PlatformImpactView(APIView):
    """
    Public platform-level impact and summary metrics.

    Calculation Assumptions:
    - total_meals_served: Sum of estimated 'servings' across COMPLETED and DELIVERED food donations.
    - food_rescued_kg_estimate: Direct 'kg' donations summed, plus meals calculated at an average
      nutritional standard of 0.4 kg per meal (source: FAO / Food Waste Index guideline).
    - completion_rate: Completed donations divided by total closed (completed + cancelled) donations.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_donations = FoodDonation.objects.count()

        available_count = FoodDonation.objects.filter(
            status__in=[DonationStatus.AVAILABLE, DonationStatus.REQUESTED]
        ).count()

        completed_donations = FoodDonation.objects.filter(
            status__in=[DonationStatus.DELIVERED, DonationStatus.COMPLETED]
        )
        completed_count = completed_donations.count()

        cancelled_count = FoodDonation.objects.filter(
            status__in=[DonationStatus.CANCELLED, DonationStatus.EXPIRED]
        ).count()

        # Servings calculations
        servings_sum = completed_donations.aggregate(total=Sum("servings"))["total"] or 0

        # Kg estimate calculations:
        kg_from_kg_units = (
            completed_donations.filter(unit="kg").aggregate(total=Sum("quantity"))["total"] or 0
        )
        # 0.4 kg per meal assumption
        kg_from_servings = float(servings_sum) * 0.4
        total_kg_rescued = round(float(kg_from_kg_units) + kg_from_servings, 1)

        # Community users
        donor_count = User.objects.filter(role=UserRole.DONOR, is_active=True).count()
        ngo_count = User.objects.filter(role=UserRole.NGO_RECEIVER, is_active=True).count()
        volunteer_count = User.objects.filter(role=UserRole.VOLUNTEER, is_active=True).count()

        # Completion rate
        closed_total = completed_count + cancelled_count
        completion_rate = round((completed_count / closed_total) * 100, 1) if closed_total > 0 else 100.0

        # Recent completed activities
        recent_activity = [
            {
                "id": d.id,
                "title": d.title,
                "donor_name": d.donor.full_name,
                "city": d.pickup_city,
                "servings": d.servings,
                "completed_at": d.updated_at,
            }
            for d in completed_donations.select_related("donor").order_by("-updated_at")[:5]
        ]

        return Response({
            "metrics": {
                "total_donations": total_donations,
                "available_donations": available_count,
                "completed_donations": completed_count,
                "cancelled_donations": cancelled_count,
                "meals_rescued": servings_sum,
                "food_rescued_kg_estimate": total_kg_rescued,
                "completion_rate_percentage": completion_rate,
            },
            "community": {
                "active_donors": donor_count,
                "registered_ngos": ngo_count,
                "delivery_volunteers": volunteer_count,
            },
            "assumptions": {
                "meals_calculation": "Sum of servings from completed distributions.",
                "kg_calculation": "Direct kg donations + standard average of 0.4 kg per meal serving.",
            },
            "recent_activity": recent_activity,
        })


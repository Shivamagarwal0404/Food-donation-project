"""
FoodShare — Pickups views.
Handles volunteer dispatching, task acceptance, and fulfillment status updates.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.users.models import UserRole
from apps.users.permissions import is_admin_or_staff
from apps.donations.models import DonationRequest
from .models import Pickup, PickupStatus
from .serializers import PickupSerializer


class PickupListView(generics.ListAPIView):
    """
    List pickups with strict role-based visibility:
    - Admin: All pickups
    - Donor: Pickups for donations they posted
    - NGO: Pickups for donations they successfully claimed
    - Volunteer: Pickups assigned to them or available for pickup
    """

    serializer_class = PickupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Pickup.objects.select_related("donation", "donation__donor", "donation__category", "volunteer")
            .order_by("-created_at")
        )

        if is_admin_or_staff(user):
            return qs

        if user.is_donor:
            return qs.filter(donation__donor=user)

        if user.is_ngo:
            accepted_donation_ids = DonationRequest.objects.filter(
                receiver=user,
                status=DonationRequest.RequestStatus.ACCEPTED,
            ).values_list("donation_id", flat=True)
            return qs.filter(donation_id__in=accepted_donation_ids)

        if user.is_volunteer:
            return qs.filter(
                models_q_filter := (
                    models_q_filter_expr(user)
                )
            )

        return qs.none()


def models_q_filter_expr(user):
    from django.db.models import Q
    return Q(volunteer=user) | Q(status=PickupStatus.PENDING)


class PickupDetailView(generics.RetrieveAPIView):
    """
    Retrieve pickup detail with role-based access validation:
    - Admin: Any pickup
    - Donor: Must be donation owner
    - NGO: Must be accepted requester
    - Volunteer: Must be assigned volunteer or pickup must be PENDING
    """

    queryset = Pickup.objects.select_related(
        "donation", "donation__donor", "donation__category", "volunteer"
    )
    serializer_class = PickupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        pickup = super().get_object()
        user = self.request.user

        if is_admin_or_staff(user):
            return pickup

        if user.is_donor and pickup.donation.donor == user:
            return pickup

        if user.is_ngo:
            has_accepted_claim = DonationRequest.objects.filter(
                donation=pickup.donation,
                receiver=user,
                status=DonationRequest.RequestStatus.ACCEPTED,
            ).exists()
            if has_accepted_claim:
                return pickup

        if user.is_volunteer and (pickup.volunteer == user or pickup.status == PickupStatus.PENDING):
            return pickup

        raise PermissionDenied("You do not have permission to view this pickup.")


class AvailablePickupsListView(generics.ListAPIView):
    """List pickups awaiting volunteer assignment."""

    serializer_class = PickupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Pickup.objects.filter(status=PickupStatus.PENDING)
            .select_related("donation", "donation__donor", "donation__category")
            .order_by("-created_at")
        )


class MyPickupsListView(generics.ListAPIView):
    """List pickups assigned to the logged-in volunteer."""

    serializer_class = PickupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Pickup.objects.filter(volunteer=self.request.user)
            .select_related("donation", "donation__donor", "donation__category")
            .order_by("-created_at")
        )


class PickupAssignView(APIView):
    """
    Volunteer assigns themselves to an unassigned pickup.
    Uses select_for_update() to prevent race conditions during concurrent claiming.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not (user.is_volunteer or is_admin_or_staff(user)):
            raise PermissionDenied("Only registered volunteers can accept pickup tasks.")

        with transaction.atomic():
            pickup = (
                Pickup.objects.select_for_update()
                .select_related("donation")
                .filter(pk=pk)
                .first()
            )
            if not pickup:
                return Response(
                    {"error": "Pickup not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if pickup.status != PickupStatus.PENDING or pickup.volunteer is not None:
                return Response(
                    {"error": f"Pickup is not available for assignment (current status: {pickup.status})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                pickup.assign_volunteer(user)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Successfully assigned pickup to {user.full_name}.",
                "pickup": PickupSerializer(pickup).data,
            },
            status=status.HTTP_200_OK,
        )


class PickupMarkPickedUpView(APIView):
    """
    Assigned volunteer marks food as picked up from donor location.
    Transitions: ASSIGNED -> PICKED_UP.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        pickup = get_object_or_404(Pickup.objects.select_related("donation", "volunteer"), pk=pk)
        user = request.user

        if pickup.volunteer != user and not is_admin_or_staff(user):
            raise PermissionDenied("You are not the assigned volunteer for this pickup.")

        if pickup.status == PickupStatus.COMPLETED:
            return Response(
                {"error": "Completed pickup cannot be modified back to an earlier state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pickup.status != PickupStatus.ASSIGNED:
            return Response(
                {"error": f"Cannot mark food picked up from status '{pickup.status}' (must be ASSIGNED)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                pickup.mark_picked_up()
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Food successfully marked as picked up.",
                "pickup": PickupSerializer(pickup).data,
            },
            status=status.HTTP_200_OK,
        )


class PickupMarkDeliveredView(APIView):
    """
    Assigned volunteer marks food as delivered to NGO location.
    Transitions: PICKED_UP -> DELIVERED.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        pickup = get_object_or_404(Pickup.objects.select_related("donation", "volunteer"), pk=pk)
        user = request.user

        if pickup.volunteer != user and not is_admin_or_staff(user):
            raise PermissionDenied("You are not the assigned volunteer for this pickup.")

        if pickup.status == PickupStatus.COMPLETED:
            return Response(
                {"error": "Completed pickup cannot be modified back to an earlier state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pickup.status != PickupStatus.PICKED_UP:
            return Response(
                {"error": f"Cannot mark food delivered from status '{pickup.status}' (must be PICKED_UP)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                pickup.mark_delivered()
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Food successfully marked as delivered.",
                "pickup": PickupSerializer(pickup).data,
            },
            status=status.HTTP_200_OK,
        )


class PickupMarkCompletedView(APIView):
    """
    Assigned volunteer or platform admin verifies delivery completion.
    Transitions: DELIVERED -> COMPLETED.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        pickup = get_object_or_404(Pickup.objects.select_related("donation", "volunteer"), pk=pk)
        user = request.user

        if pickup.volunteer != user and not is_admin_or_staff(user):
            raise PermissionDenied("You are not the assigned volunteer for this pickup.")

        if pickup.status == PickupStatus.COMPLETED:
            return Response(
                {"error": "Pickup is already marked as completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pickup.status != PickupStatus.DELIVERED:
            return Response(
                {"error": f"Cannot complete pickup from status '{pickup.status}' (must be DELIVERED)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                pickup.mark_completed()
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Pickup successfully marked as completed.",
                "pickup": PickupSerializer(pickup).data,
            },
            status=status.HTTP_200_OK,
        )


class PickupStatusUpdateView(APIView):
    """
    Backward-compatible unified status update endpoint:
    - PICKED_UP
    - DELIVERED
    - COMPLETED
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        pickup = get_object_or_404(Pickup.objects.select_related("donation", "volunteer"), pk=pk)
        user = request.user

        if pickup.volunteer != user and not is_admin_or_staff(user):
            raise PermissionDenied("You are not the assigned volunteer for this pickup.")

        if pickup.status == PickupStatus.COMPLETED:
            return Response(
                {"error": "Completed pickup cannot be modified back to an earlier state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_status = request.data.get("status")
        valid_targets = [
            PickupStatus.PICKED_UP,
            PickupStatus.DELIVERED,
            PickupStatus.COMPLETED,
        ]
        if target_status not in valid_targets:
            return Response(
                {"error": f"Invalid target status '{target_status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                if target_status == PickupStatus.PICKED_UP:
                    pickup.mark_picked_up()
                elif target_status == PickupStatus.DELIVERED:
                    pickup.mark_delivered()
                elif target_status == PickupStatus.COMPLETED:
                    pickup.mark_completed()
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Pickup status updated to {pickup.status}.",
                "pickup": PickupSerializer(pickup).data,
            },
            status=status.HTTP_200_OK,
        )

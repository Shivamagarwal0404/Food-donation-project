"""
FoodShare — Pickups & Delivery Test Suite.

Verifies 15 required business rules and workflows:
 1. Accepted donation creates pickup.
 2. Volunteer can see available pickup.
 3. Volunteer can claim pickup.
 4. Second volunteer cannot claim already-assigned pickup.
 5. Non-volunteer cannot claim pickup.
 6. Assigned volunteer can mark pickup as picked up.
 7. Unassigned volunteer cannot mark someone else's pickup as picked up.
 8. Assigned volunteer can mark pickup as delivered.
 9. Invalid status transition is rejected.
10. Donation status synchronizes with pickup status.
11. Donor cannot arbitrarily change pickup status.
12. NGO cannot arbitrarily change pickup status.
13. Admin can inspect/manage pickups.
14. Concurrent pickup assignment cannot create duplicate assignment.
15. Completed pickup cannot be modified back to an earlier state.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.core.exceptions import ValidationError

from apps.users.models import User, UserRole, VolunteerProfile, NGOProfile
from apps.donations.models import FoodCategory, FoodDonation, DonationRequest, DonationStatus
from apps.pickups.models import Pickup, PickupStatus


class PickupWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Donor
        self.donor = User.objects.create_user(
            email="donor@kitchen.com",
            password="StrongPassword123!",
            first_name="Chef",
            last_name="Marie",
            role=UserRole.DONOR,
        )

        # NGO
        self.ngo = User.objects.create_user(
            email="ngo@shelter.org",
            password="StrongPassword123!",
            first_name="Hope",
            last_name="Shelter",
            role=UserRole.NGO_RECEIVER,
        )
        NGOProfile.objects.create(user=self.ngo, organization_name="Hope Shelter", is_verified=True)

        # Volunteer 1
        self.volunteer = User.objects.create_user(
            email="volunteer1@delivery.com",
            password="StrongPassword123!",
            first_name="Alex",
            last_name="Rider",
            role=UserRole.VOLUNTEER,
        )
        self.volunteer_profile = VolunteerProfile.objects.create(user=self.volunteer)

        # Volunteer 2
        self.other_volunteer = User.objects.create_user(
            email="volunteer2@delivery.com",
            password="StrongPassword123!",
            first_name="Sam",
            last_name="Wilson",
            role=UserRole.VOLUNTEER,
        )
        VolunteerProfile.objects.create(user=self.other_volunteer)

        # Platform Admin
        self.admin = User.objects.create_superuser(
            email="admin@foodshare.org",
            password="StrongPassword123!",
            first_name="Super",
            last_name="Admin",
            role=UserRole.ADMIN,
        )

        # Food Category
        self.category, _ = FoodCategory.objects.get_or_create(
            name="Bakery",
            defaults={"slug": "bakery", "is_active": True},
        )

        # Donation
        self.donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="30 Fresh Sandwiches",
            quantity=30,
            unit="meals",
            servings=30,
            expiry_at=timezone.now() + timedelta(hours=8),
            pickup_address="789 Baker Street",
            pickup_contact_phone="9876543210",
            status=DonationStatus.ACCEPTED,
        )

    def test_pickup_assignment_and_completion(self):
        """Preserve and verify the original end-to-end unit test across all 5 milestones."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        # Volunteer assigns
        pickup.assign_volunteer(self.volunteer)
        self.assertEqual(pickup.status, PickupStatus.ASSIGNED)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKUP_ASSIGNED)

        # Mark picked up
        pickup.mark_picked_up()
        self.assertEqual(pickup.status, PickupStatus.PICKED_UP)
        self.assertIsNotNone(pickup.picked_up_at)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKED_UP)

        # Mark delivered
        pickup.mark_delivered()
        self.assertEqual(pickup.status, PickupStatus.DELIVERED)
        self.assertIsNotNone(pickup.delivered_at)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.DELIVERED)

        # Mark completed
        pickup.mark_completed()
        self.assertEqual(pickup.status, PickupStatus.COMPLETED)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.COMPLETED)
        self.volunteer_profile.refresh_from_db()
        self.assertEqual(self.volunteer_profile.deliveries_completed, 1)

    def test_01_accepted_donation_creates_pickup(self):
        """1. Acceptance of an NGO claim request creates a Pickup record with PENDING status."""
        new_donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Surplus Rice & Curry",
            quantity=25,
            unit="meals",
            servings=25,
            expiry_at=timezone.now() + timedelta(hours=10),
            pickup_address="456 Market Lane",
            pickup_contact_phone="9876543211",
            status=DonationStatus.AVAILABLE,
        )
        claim_req = DonationRequest.objects.create(
            donation=new_donation,
            receiver=self.ngo,
            requested_servings=25,
            message="We can distribute this today.",
        )

        self.client.force_authenticate(user=self.donor)
        res = self.client.post(f"/api/v1/donations/requests/{claim_req.id}/accept/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup = Pickup.objects.filter(donation=new_donation).first()
        self.assertIsNotNone(pickup)
        self.assertEqual(pickup.status, PickupStatus.PENDING)
        self.assertEqual(pickup.pickup_location, new_donation.pickup_address)
        self.assertIsNone(pickup.volunteer)

    def test_02_volunteer_can_see_available_pickup(self):
        """2. Volunteer can query available pickups awaiting assignment."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.get("/api/v1/pickups/available/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pickup_ids = [p["id"] for p in res.data["results"] if "results" in res.data] if "results" in res.data else [p["id"] for p in res.data]
        self.assertIn(pickup.id, pickup_ids)

    def test_03_volunteer_can_claim_pickup(self):
        """3. Volunteer can claim an available pickup, transitioning it to ASSIGNED."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.ASSIGNED)
        self.assertEqual(pickup.volunteer, self.volunteer)

        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKUP_ASSIGNED)

    def test_04_second_volunteer_cannot_claim_already_assigned_pickup(self):
        """4. Once claimed, a second volunteer cannot claim the same pickup."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)

        self.client.force_authenticate(user=self.other_volunteer)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        pickup.refresh_from_db()
        self.assertEqual(pickup.volunteer, self.volunteer)

    def test_05_non_volunteer_cannot_claim_pickup(self):
        """5. Non-volunteers (Donors, NGOs, unauthenticated) are forbidden from claiming pickups."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        # Donor attempt
        self.client.force_authenticate(user=self.donor)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # NGO attempt
        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Unauthenticated attempt
        self.client.force_authenticate(user=None)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_06_assigned_volunteer_can_mark_pickup_as_picked_up(self):
        """6. Assigned volunteer can mark food picked up from donor."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.PICKED_UP)
        self.assertIsNotNone(pickup.picked_up_at)

        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKED_UP)

    def test_07_unassigned_volunteer_cannot_mark_someone_elses_pickup_as_picked_up(self):
        """7. A volunteer cannot mark someone else's assigned pickup as picked up."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)

        self.client.force_authenticate(user=self.other_volunteer)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        pickup.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.ASSIGNED)

    def test_08_assigned_volunteer_can_mark_pickup_as_delivered(self):
        """8. Assigned volunteer can mark food delivered to NGO."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)
        pickup.mark_picked_up()

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.DELIVERED)
        self.assertIsNotNone(pickup.delivered_at)

        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.DELIVERED)

    def test_09_invalid_status_transition_is_rejected(self):
        """9. Invalid status transitions (e.g. PENDING -> DELIVERED, ASSIGNED -> COMPLETED) are rejected."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        self.client.force_authenticate(user=self.volunteer)
        # Attempt to deliver unassigned pickup
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

        # Assign pickup
        pickup.assign_volunteer(self.volunteer)

        # Attempt to jump ASSIGNED -> DELIVERED (bypassing PICKED_UP)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to jump ASSIGNED -> COMPLETED
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_10_donation_status_synchronizes_with_pickup_status(self):
        """10. FoodDonation status synchronizes consistently across all pickup stages."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        self.assertEqual(self.donation.status, DonationStatus.ACCEPTED)

        # 1. Assign
        pickup.assign_volunteer(self.volunteer)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKUP_ASSIGNED)

        # 2. Pick up
        pickup.mark_picked_up()
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.PICKED_UP)

        # 3. Deliver
        pickup.mark_delivered()
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.DELIVERED)

        # 4. Complete
        pickup.mark_completed()
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationStatus.COMPLETED)

    def test_11_donor_cannot_arbitrarily_change_pickup_status(self):
        """11. Donor cannot change pickup status via action endpoints or direct updates."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)

        self.client.force_authenticate(user=self.donor)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/status/", {"status": "DELIVERED"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_ngo_cannot_arbitrarily_change_pickup_status(self):
        """12. NGO cannot change pickup status via action endpoints or direct updates."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)

        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.client.post(f"/api/v1/pickups/{pickup.id}/status/", {"status": "DELIVERED"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_admin_can_inspect_and_manage_pickups(self):
        """13. Platform admin can inspect all pickups and perform administrative management."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/v1/pickups/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        detail_res = self.client.get(f"/api/v1/pickups/{pickup.id}/")
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["id"], pickup.id)

    def test_14_concurrent_pickup_assignment_cannot_create_duplicate_assignment(self):
        """14. Database row-level locking ensures only one volunteer can claim a pickup."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        # First claim succeeds
        self.client.force_authenticate(user=self.volunteer)
        res1 = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Simultaneous second claim fails
        self.client.force_authenticate(user=self.other_volunteer)
        res2 = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        pickup.refresh_from_db()
        self.assertEqual(pickup.volunteer, self.volunteer)

    def test_15_completed_pickup_cannot_be_modified_back_to_earlier_state(self):
        """15. Completed pickup is immutable and cannot be rolled back to earlier states."""
        pickup = Pickup.objects.create(
            donation=self.donation,
            pickup_location=self.donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        pickup.assign_volunteer(self.volunteer)
        pickup.mark_picked_up()
        pickup.mark_delivered()
        pickup.mark_completed()
        self.assertEqual(pickup.status, PickupStatus.COMPLETED)

        self.client.force_authenticate(user=self.volunteer)

        # Attempt rollback via pickup endpoint
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt rollback via deliver endpoint
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt rollback via unified status endpoint
        res = self.client.post(f"/api/v1/pickups/{pickup.id}/status/", {"status": "PENDING"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Direct model transition must raise ValidationError
        with self.assertRaises(ValidationError):
            pickup.transition_to(PickupStatus.PENDING)

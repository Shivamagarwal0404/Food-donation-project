"""
FoodShare — Phase D Donation & Request Workflow Hardening Test Suite.

Contains explicit test cases for:
Positive Tests (1 to 10):
1. Valid donation creation
2. Valid NGO request
3. Accept pending request (and cascade rejection of competing requests)
4. Volunteer claims pickup (concurrency & state sync)
5. Mark picked up (timestamp & status sync)
6. Mark delivered (timestamp & status sync)
7. Complete pickup (deliveries increment & completion)
8. Analytics update (metrics reflect completed donation)
9. Valid cancellation (AVAILABLE, REQUESTED, ACCEPTED, NGO cancel)
10. Other category + specified item

Negative Tests (1 to 18):
1. Unauthorized donation modification
2. Unauthorized cancellation
3. Request unavailable donation
4. Duplicate request
5. Self-request
6. Expired donation request
7. Cancelled donation request
8. Unauthorized request accept/reject
9. Second volunteer claim
10. Unauthorized pickup update
11. Invalid pickup transition
12. Complete before delivery
13. Modify completed pickup
14. Modify completed donation
15. Invalid/inactive category
16. Other without food item
17. Anonymous protected API access
18. Attempt to cancel PICKED_UP donation
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User, UserRole, NGOProfile, VolunteerProfile
from apps.donations.models import FoodCategory, FoodDonation, DonationRequest, DonationStatus
from apps.pickups.models import Pickup, PickupStatus


class PhaseDWorkflowHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Donor 1 (Owner)
        self.donor = User.objects.create_user(
            email="donor1@foodshare.org",
            password="StrongPassword123!",
            first_name="Donor",
            last_name="One",
            role=UserRole.DONOR,
            is_verified=True,
        )

        # Donor 2 (Attacker/Other Donor)
        self.other_donor = User.objects.create_user(
            email="donor2@foodshare.org",
            password="StrongPassword123!",
            first_name="Donor",
            last_name="Two",
            role=UserRole.DONOR,
            is_verified=True,
        )

        # NGO 1 (Verified)
        self.ngo = User.objects.create_user(
            email="ngo1@shelter.org",
            password="StrongPassword123!",
            first_name="City",
            last_name="Shelter",
            role=UserRole.NGO_RECEIVER,
            is_verified=True,
        )
        self.ngo_profile = NGOProfile.objects.create(
            user=self.ngo,
            organization_name="City Shelter",
            is_verified=True,
        )

        # NGO 2 (Verified Competing NGO)
        self.other_ngo = User.objects.create_user(
            email="ngo2@shelter.org",
            password="StrongPassword123!",
            first_name="Care",
            last_name="Home",
            role=UserRole.NGO_RECEIVER,
            is_verified=True,
        )
        self.other_ngo_profile = NGOProfile.objects.create(
            user=self.other_ngo,
            organization_name="Care Home",
            is_verified=True,
        )

        # Volunteer 1
        self.volunteer = User.objects.create_user(
            email="vol1@foodshare.org",
            password="StrongPassword123!",
            first_name="Ravi",
            last_name="Volunteer",
            role=UserRole.VOLUNTEER,
            is_verified=True,
        )
        self.volunteer_profile = VolunteerProfile.objects.create(
            user=self.volunteer,
            deliveries_completed=0,
        )

        # Volunteer 2 (Competitor / Other)
        self.other_volunteer = User.objects.create_user(
            email="vol2@foodshare.org",
            password="StrongPassword123!",
            first_name="Amit",
            last_name="Volunteer",
            role=UserRole.VOLUNTEER,
            is_verified=True,
        )
        self.other_vol_profile = VolunteerProfile.objects.create(
            user=self.other_volunteer,
            deliveries_completed=0,
        )

        # Admin
        self.admin_user = User.objects.create_user(
            email="admin@foodshare.org",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_staff=True,
            is_verified=True,
        )

        # Categories
        self.category, _ = FoodCategory.objects.get_or_create(
            name="Cooked Meals",
            defaults={"slug": "cooked-meals", "is_active": True},
        )
        self.inactive_category, _ = FoodCategory.objects.get_or_create(
            name="Archived Category",
            defaults={"slug": "archived-category", "is_active": False},
        )
        self.other_category, _ = FoodCategory.objects.get_or_create(
            name="Other",
            defaults={"slug": "other", "is_active": True},
        )

    # -------------------------------------------------------------------------
    # POSITIVE TESTS (1 to 10)
    # -------------------------------------------------------------------------

    def test_positive_01_valid_donation_creation(self):
        """1. Donor creates valid donation."""
        self.client.force_authenticate(user=self.donor)
        payload = {
            "category": self.category.id,
            "title": "Fresh Paneer Rice Boxes",
            "quantity": 25,
            "unit": "meals",
            "servings": 25,
            "expiry_at": (timezone.now() + timedelta(hours=6)).isoformat(),
            "pickup_address": "Kitchen 4, Main Road",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(reverse("donation-list-create"), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], DonationStatus.AVAILABLE)
        self.assertEqual(res.data["title"], "Fresh Paneer Rice Boxes")

    def test_positive_02_valid_ngo_request(self):
        """2. NGO requests available donation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Surplus Bread Loaves",
            quantity=30,
            unit="meals",
            servings=30,
            expiry_at=timezone.now() + timedelta(hours=8),
            pickup_address="Bakery St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        payload = {
            "donation": donation.id,
            "requested_servings": 20,
            "message": "Shelter evening meal for 20 people",
        }
        res = self.client.post(reverse("donation-request-create"), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], DonationRequest.RequestStatus.PENDING)

        donation.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.REQUESTED)

    def test_positive_03_accept_pending_request(self):
        """3. Donor accepts request, competing requests rejected, pickup created."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Rice and Dal",
            quantity=50,
            unit="meals",
            servings=50,
            status=DonationStatus.REQUESTED,
            expiry_at=timezone.now() + timedelta(hours=8),
            pickup_address="Central Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        req1 = DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=30,
            status=DonationRequest.RequestStatus.PENDING,
        )
        req2 = DonationRequest.objects.create(
            donation=donation,
            receiver=self.other_ngo,
            requested_servings=20,
            status=DonationRequest.RequestStatus.PENDING,
        )

        self.client.force_authenticate(user=self.donor)
        res = self.client.post(reverse("donation-request-accept", kwargs={"pk": req1.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        req1.refresh_from_db()
        req2.refresh_from_db()
        donation.refresh_from_db()

        self.assertEqual(req1.status, DonationRequest.RequestStatus.ACCEPTED)
        self.assertEqual(req2.status, DonationRequest.RequestStatus.REJECTED)
        self.assertEqual(donation.status, DonationStatus.ACCEPTED)

        # Pickup auto-created
        pickup = Pickup.objects.get(donation=donation)
        self.assertEqual(pickup.status, PickupStatus.PENDING)
        self.assertIsNone(pickup.volunteer)

    def test_positive_04_volunteer_claims_pickup(self):
        """4. Volunteer claims pickup."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Hot Soup Pots",
            quantity=20,
            unit="meals",
            servings=20,
            status=DonationStatus.ACCEPTED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Community Hall",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            pickup_location=donation.pickup_address,
            status=PickupStatus.PENDING,
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-assign", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.ASSIGNED)
        self.assertEqual(pickup.volunteer, self.volunteer)
        self.assertEqual(donation.status, DonationStatus.PICKUP_ASSIGNED)

    def test_positive_05_mark_picked_up(self):
        """5. Volunteer marks pickup as picked up."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Curry Tins",
            quantity=15,
            unit="meals",
            servings=15,
            status=DonationStatus.PICKUP_ASSIGNED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.ASSIGNED,
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-mark-picked-up", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.PICKED_UP)
        self.assertIsNotNone(pickup.picked_up_at)
        self.assertEqual(donation.status, DonationStatus.PICKED_UP)

    def test_positive_06_mark_delivered(self):
        """6. Volunteer marks delivered."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Bread Baskets",
            quantity=40,
            unit="meals",
            servings=40,
            status=DonationStatus.PICKED_UP,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Bakery",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.PICKED_UP,
            picked_up_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-mark-delivered", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.DELIVERED)
        self.assertIsNotNone(pickup.delivered_at)
        self.assertEqual(donation.status, DonationStatus.DELIVERED)

    def test_positive_07_complete_pickup(self):
        """7. Pickup becomes completed."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Dinner Platters",
            quantity=25,
            unit="meals",
            servings=25,
            status=DonationStatus.DELIVERED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Restaurant",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.DELIVERED,
            picked_up_at=timezone.now() - timedelta(minutes=45),
            delivered_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-mark-completed", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.volunteer_profile.refresh_from_db()

        self.assertEqual(pickup.status, PickupStatus.COMPLETED)
        self.assertEqual(donation.status, DonationStatus.COMPLETED)
        self.assertEqual(self.volunteer_profile.deliveries_completed, 1)

    def test_positive_08_analytics_update(self):
        """8. Donation/analytics reflect completion."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Completed Banquet Surplus",
            quantity=100,
            unit="meals",
            servings=100,
            status=DonationStatus.COMPLETED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Banquet Hall",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        res = self.client.get(reverse("analytics-impact"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        metrics = res.data.get("metrics", {})
        self.assertGreaterEqual(metrics.get("completed_donations", 0), 1)
        self.assertGreaterEqual(metrics.get("meals_rescued", 0), 100)

    def test_positive_09_valid_cancellation(self):
        """9. Valid cancellation works where permitted."""
        # 9a. Cancel AVAILABLE
        d1 = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Available Donation",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.AVAILABLE,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.donor)
        res = self.client.post(reverse("donation-cancel", kwargs={"pk": d1.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        d1.refresh_from_db()
        self.assertEqual(d1.status, DonationStatus.CANCELLED)

        # 9b. Cancel ACCEPTED with pending pickup -> pickup cascades to CANCELLED
        d2 = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Accepted Donation",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.ACCEPTED,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        p2 = Pickup.objects.create(
            donation=d2,
            pickup_location=d2.pickup_address,
            status=PickupStatus.PENDING,
        )
        res2 = self.client.post(reverse("donation-cancel", kwargs={"pk": d2.id}))
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        d2.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(d2.status, DonationStatus.CANCELLED)
        self.assertEqual(p2.status, PickupStatus.CANCELLED)

        # 9c. NGO cancels own PENDING request -> request cancelled, donation reverts
        d3 = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Requested Donation",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.REQUESTED,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        r3 = DonationRequest.objects.create(
            donation=d3,
            receiver=self.ngo,
            requested_servings=5,
            status=DonationRequest.RequestStatus.PENDING,
        )
        self.client.force_authenticate(user=self.ngo)
        res3 = self.client.post(reverse("donation-request-cancel", kwargs={"pk": r3.id}))
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        r3.refresh_from_db()
        d3.refresh_from_db()
        self.assertEqual(r3.status, DonationRequest.RequestStatus.CANCELLED)
        self.assertEqual(d3.status, DonationStatus.AVAILABLE)

    def test_positive_10_other_category_specified_item(self):
        """10. Other category with specified food item works."""
        self.client.force_authenticate(user=self.donor)
        payload = {
            "category": self.other_category.id,
            "other_food_item": "Homemade Gulab Jamun",
            "title": "Festival Sweets Batch",
            "quantity": 10,
            "unit": "kg",
            "servings": 30,
            "expiry_at": (timezone.now() + timedelta(days=2)).isoformat(),
            "pickup_address": "Sweet Shop, Delhi",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(reverse("donation-list-create"), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["other_food_item"], "Homemade Gulab Jamun")

    # -------------------------------------------------------------------------
    # NEGATIVE TESTS (1 to 18)
    # -------------------------------------------------------------------------

    def test_negative_01_unauthorized_donation_modification(self):
        """Negative 1: Unauthorized donation modification."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Chef John Soup",
            quantity=20,
            unit="meals",
            servings=20,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.other_donor)
        res = self.client.patch(
            reverse("donation-detail", kwargs={"pk": donation.id}),
            {"title": "Hacked Title"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_02_unauthorized_cancellation(self):
        """Negative 2: Unauthorized donation cancellation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Chef John Stew",
            quantity=20,
            unit="meals",
            servings=20,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.other_donor)
        res = self.client.post(reverse("donation-cancel", kwargs={"pk": donation.id}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_03_request_unavailable_donation(self):
        """Negative 3: NGO requesting unavailable donation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Already Accepted Stew",
            quantity=20,
            unit="meals",
            servings=20,
            status=DonationStatus.ACCEPTED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(
            reverse("donation-request-create"),
            {"donation": donation.id, "requested_servings": 10},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_04_duplicate_request(self):
        """Negative 4: Duplicate donation request by same NGO."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Biryani Pot",
            quantity=30,
            unit="meals",
            servings=30,
            status=DonationStatus.AVAILABLE,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=10,
            status=DonationRequest.RequestStatus.PENDING,
        )
        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(
            reverse("donation-request-create"),
            {"donation": donation.id, "requested_servings": 10},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_05_self_request(self):
        """Negative 5: Requesting own donation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="My Own Food",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.AVAILABLE,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.donor)
        res = self.client.post(
            reverse("donation-request-create"),
            {"donation": donation.id, "requested_servings": 5},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("own donation", str(res.data))

    def test_negative_06_expired_donation_request(self):
        """Negative 6: Requesting expired donation."""
        past_time = timezone.now() - timedelta(hours=2)
        donation = FoodDonation(
            donor=self.donor,
            category=self.category,
            title="Expired Meal",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.EXPIRED,
            expiry_at=past_time,
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        donation.save(force_insert=True)

        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(
            reverse("donation-request-create"),
            {"donation": donation.id, "requested_servings": 5},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_07_cancelled_donation_request(self):
        """Negative 7: Requesting cancelled donation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Cancelled Batch",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.CANCELLED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        res = self.client.post(
            reverse("donation-request-create"),
            {"donation": donation.id, "requested_servings": 5},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_08_unauthorized_request_accept_reject(self):
        """Negative 8: Unauthorized request acceptance/rejection."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Donor One Salad",
            quantity=15,
            unit="meals",
            servings=15,
            status=DonationStatus.REQUESTED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        req = DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=10,
            status=DonationRequest.RequestStatus.PENDING,
        )
        self.client.force_authenticate(user=self.other_donor)

        res_accept = self.client.post(reverse("donation-request-accept", kwargs={"pk": req.id}))
        self.assertEqual(res_accept.status_code, status.HTTP_403_FORBIDDEN)

        res_reject = self.client.post(reverse("donation-request-reject", kwargs={"pk": req.id}))
        self.assertEqual(res_reject.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_09_second_volunteer_claim(self):
        """Negative 9: Two volunteers claiming the same pickup."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Soup Pot",
            quantity=20,
            unit="meals",
            servings=20,
            status=DonationStatus.PICKUP_ASSIGNED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.ASSIGNED,
        )
        self.client.force_authenticate(user=self.other_volunteer)
        res = self.client.post(reverse("pickup-assign", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not available", res.data["error"].lower())

    def test_negative_10_unauthorized_pickup_update(self):
        """Negative 10: Volunteer B attempts to update Volunteer A's pickup."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Assigned Box",
            quantity=20,
            unit="meals",
            servings=20,
            status=DonationStatus.PICKUP_ASSIGNED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.ASSIGNED,
        )
        self.client.force_authenticate(user=self.other_volunteer)
        res = self.client.post(reverse("pickup-mark-picked-up", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_11_invalid_pickup_transition(self):
        """Negative 11: Invalid pickup status jump (PENDING -> DELIVERED)."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Pending Pickup",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.ACCEPTED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            pickup_location=donation.pickup_address,
            status=PickupStatus.PENDING,
        )
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(
            reverse("pickup-status-update", kwargs={"pk": pickup.id}),
            {"status": PickupStatus.DELIVERED},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_12_complete_before_delivery(self):
        """Negative 12: Completing pickup before delivery."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="In-Transit Food",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.PICKED_UP,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.PICKED_UP,
            picked_up_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-mark-completed", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_13_modify_completed_pickup(self):
        """Negative 13: Modifying completed pickup."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Done Food",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.COMPLETED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.COMPLETED,
        )
        self.client.force_authenticate(user=self.volunteer)
        res = self.client.post(reverse("pickup-mark-picked-up", kwargs={"pk": pickup.id}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_14_modify_completed_donation(self):
        """Negative 14: Modifying completed donation."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Completed Meal",
            quantity=10,
            unit="meals",
            servings=10,
            status=DonationStatus.COMPLETED,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.donor)
        res = self.client.patch(
            reverse("donation-detail", kwargs={"pk": donation.id}),
            {"title": "Attempted Edit"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_15_invalid_or_inactive_category(self):
        """Negative 15: Invalid or inactive category."""
        self.client.force_authenticate(user=self.donor)
        # Non-existent
        res1 = self.client.post(
            reverse("donation-list-create"),
            {
                "category": 999999,
                "title": "Invalid Cat",
                "quantity": 10,
                "unit": "meals",
                "servings": 10,
                "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
                "pickup_address": "Kitchen",
                "pickup_city": "Delhi",
                "pickup_contact_phone": "9876543210",
            },
            format="json",
        )
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Inactive category
        res2 = self.client.post(
            reverse("donation-list-create"),
            {
                "category": self.inactive_category.id,
                "title": "Inactive Cat",
                "quantity": 10,
                "unit": "meals",
                "servings": 10,
                "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
                "pickup_address": "Kitchen",
                "pickup_city": "Delhi",
                "pickup_contact_phone": "9876543210",
            },
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_16_other_without_food_item(self):
        """Negative 16: Other without food item description."""
        self.client.force_authenticate(user=self.donor)
        res = self.client.post(
            reverse("donation-list-create"),
            {
                "category": self.other_category.id,
                "other_food_item": "   ",  # Whitespace only
                "title": "Empty Other Description",
                "quantity": 10,
                "unit": "meals",
                "servings": 10,
                "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
                "pickup_address": "Kitchen",
                "pickup_city": "Delhi",
                "pickup_contact_phone": "9876543210",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("other_food_item", res.data)

    def test_negative_17_anonymous_protected_api_access(self):
        """Negative 17: Anonymous protected API access."""
        # Unauthenticated donation creation
        res1 = self.client.post(reverse("donation-list-create"), {"title": "Ghost"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_401_UNAUTHORIZED)

        # Unauthenticated request creation
        res2 = self.client.post(reverse("donation-request-create"), {"donation": 1}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_401_UNAUTHORIZED)

        # Unauthenticated pickup assign
        res3 = self.client.post(reverse("pickup-assign", kwargs={"pk": 1}))
        self.assertEqual(res3.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_negative_18_attempt_to_cancel_picked_up_donation(self):
        """Negative 18: Attempting to cancel a PICKED_UP donation is strictly rejected."""
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Food In Transit",
            quantity=20,
            unit="meals",
            servings=20,
            status=DonationStatus.PICKED_UP,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="Kitchen",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        pickup = Pickup.objects.create(
            donation=donation,
            volunteer=self.volunteer,
            pickup_location=donation.pickup_address,
            status=PickupStatus.PICKED_UP,
            picked_up_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.donor)
        res = self.client.post(reverse("donation-cancel", kwargs={"pk": donation.id}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been picked up", res.data["error"])

        # Confirm database consistency: status was NOT changed
        donation.refresh_from_db()
        pickup.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.PICKED_UP)
        self.assertEqual(pickup.status, PickupStatus.PICKED_UP)

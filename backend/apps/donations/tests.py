"""
FoodShare — Donations Test Suite.

Verifies 15 required business rules and workflows:
1. Donor can create donation.
2. NGO cannot create donation.
3. Unauthenticated user cannot create donation.
4. Donor can view own donations.
5. Donor cannot modify another donor's donation.
6. NGO can view available donations.
7. NGO can request available donation.
8. NGO cannot request own donation.
9. Duplicate active request is rejected.
10. Expired donation cannot be requested.
11. Donor can accept request.
12. Other pending requests are rejected after acceptance.
13. Invalid lifecycle transition is rejected.
14. Unauthorized status modification is rejected.
15. Donation cancellation rules work correctly.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.core.exceptions import ValidationError

from apps.users.models import User, UserRole, NGOProfile
from apps.donations.models import FoodCategory, FoodDonation, DonationRequest, DonationStatus


class FoodDonationWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Donor 1
        self.donor = User.objects.create_user(
            email="donor1@kitchen.com",
            password="StrongPassword123!",
            first_name="Chef",
            last_name="John",
            role=UserRole.DONOR,
        )

        # Donor 2
        self.other_donor = User.objects.create_user(
            email="donor2@kitchen.com",
            password="StrongPassword123!",
            first_name="Chef",
            last_name="Marie",
            role=UserRole.DONOR,
        )

        # Verified NGO
        self.ngo = User.objects.create_user(
            email="shelter@ngo.org",
            password="StrongPassword123!",
            first_name="City",
            last_name="Shelter",
            role=UserRole.NGO_RECEIVER,
        )
        self.ngo_profile = NGOProfile.objects.create(
            user=self.ngo,
            organization_name="City Hope Shelter",
            is_verified=True,
        )

        # Other Verified NGO
        self.other_ngo = User.objects.create_user(
            email="care@ngo.org",
            password="StrongPassword123!",
            first_name="Care",
            last_name="Home",
            role=UserRole.NGO_RECEIVER,
        )
        NGOProfile.objects.create(
            user=self.other_ngo,
            organization_name="Care Home",
            is_verified=True,
        )

        # Category
        self.category, _ = FoodCategory.objects.get_or_create(
            name="Cooked Meals",
            defaults={"slug": "cooked-meals", "is_active": True},
        )

    # 1. Donor can create donation
    def test_01_donor_can_create_donation(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.category.id,
            "title": "50 Servings Fresh Biryani",
            "description": "Nutritious rice and veg dish, packaged safely",
            "quantity": 50,
            "unit": "meals",
            "servings": 50,
            "expiry_at": (timezone.now() + timedelta(hours=6)).isoformat(),
            "pickup_address": "123 Main Street",
            "pickup_city": "Mumbai",
            "pickup_contact_phone": "9876543210",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FoodDonation.objects.filter(donor=self.donor).count(), 1)
        donation = FoodDonation.objects.get(donor=self.donor)
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)

    # 2. NGO cannot create donation
    def test_02_ngo_cannot_create_donation(self):
        self.client.force_authenticate(user=self.ngo)
        url = reverse("donation-list-create")
        payload = {
            "category": self.category.id,
            "title": "Unauthorized NGO Post",
            "quantity": 10,
            "unit": "meals",
            "servings": 10,
            "expiry_at": (timezone.now() + timedelta(hours=6)).isoformat(),
            "pickup_address": "456 NGO Rd",
            "pickup_contact_phone": "9876543210",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FoodDonation.objects.count(), 0)

    # 3. Unauthenticated user cannot create donation
    def test_03_unauthenticated_cannot_create_donation(self):
        url = reverse("donation-list-create")
        payload = {"title": "Anonymous Food", "quantity": 10}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 4. Donor can view own donations
    def test_04_donor_can_view_own_donations(self):
        FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Donor1 Food",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 Donor St",
            pickup_contact_phone="9876543210",
        )
        FoodDonation.objects.create(
            donor=self.other_donor,
            category=self.category,
            title="Donor2 Food",
            quantity=20,
            unit="meals",
            servings=20,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="456 Other St",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.donor)
        response = self.client.get(reverse("my-donations"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response should contain only Donor 1's donation
        data = response.data.get("results", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Donor1 Food")

    # 5. Donor cannot modify another donor's donation
    def test_05_donor_cannot_modify_another_donor_donation(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Original Food Title",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 Donor St",
            pickup_contact_phone="9876543210",
        )
        # Attempt modification as other_donor
        self.client.force_authenticate(user=self.other_donor)
        url = reverse("donation-detail", kwargs={"pk": donation.pk})
        response = self.client.patch(url, {"title": "Hacked Title"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        donation.refresh_from_db()
        self.assertEqual(donation.title, "Original Food Title")

    # 6. NGO can view available donations
    def test_06_ngo_can_view_available_donations(self):
        FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Available Meals",
            quantity=25,
            unit="meals",
            servings=25,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="123 Donor St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.AVAILABLE,
        )
        FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Completed Old Meals",
            quantity=25,
            unit="meals",
            servings=25,
            expiry_at=timezone.now() + timedelta(hours=5),
            pickup_address="123 Donor St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.COMPLETED,
        )
        self.client.force_authenticate(user=self.ngo)
        response = self.client.get(reverse("donation-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        # Default listing must show AVAILABLE / REQUESTED only
        titles = [d["title"] for d in data]
        self.assertIn("Available Meals", titles)
        self.assertNotIn("Completed Old Meals", titles)

    # 7. NGO can request available donation
    def test_07_ngo_can_request_available_donation(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Fresh Rice & Dal",
            quantity=30,
            unit="meals",
            servings=30,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 Donor St",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        url = reverse("donation-request-create")
        payload = {
            "donation": donation.pk,
            "requested_servings": 30,
            "message": "For distribution at city night shelter",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        donation.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.REQUESTED)
        self.assertEqual(donation.requests.count(), 1)

    # 8. NGO cannot request own donation
    def test_08_ngo_cannot_request_own_donation(self):
        # Create a donation where donor is also the user
        donation = FoodDonation.objects.create(
            donor=self.ngo,
            category=self.category,
            title="Self Donation",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        url = reverse("donation-request-create")
        response = self.client.post(url, {
            "donation": donation.pk,
            "requested_servings": 10,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Duplicate active request is rejected
    def test_09_duplicate_active_request_rejected(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Sandwiches",
            quantity=15,
            unit="meals",
            servings=15,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
        )
        self.client.force_authenticate(user=self.ngo)
        url = reverse("donation-request-create")

        # First request succeeds
        res1 = self.client.post(url, {"donation": donation.pk, "requested_servings": 15})
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second request from same NGO on same donation is rejected
        res2 = self.client.post(url, {"donation": donation.pk, "requested_servings": 15})
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Expired donation cannot be requested
    def test_10_expired_donation_cannot_be_requested(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Expired Bread",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() - timedelta(hours=1),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.EXPIRED,
        )
        self.client.force_authenticate(user=self.ngo)
        url = reverse("donation-request-create")
        response = self.client.post(url, {"donation": donation.pk, "requested_servings": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 11. Donor can accept request
    def test_11_donor_can_accept_request(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Hot Soup & Rolls",
            quantity=40,
            unit="meals",
            servings=40,
            expiry_at=timezone.now() + timedelta(hours=6),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.REQUESTED,
        )
        req = DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=40,
        )
        self.client.force_authenticate(user=self.donor)
        accept_url = reverse("donation-request-accept", kwargs={"pk": req.pk})
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        req.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(req.status, DonationRequest.RequestStatus.ACCEPTED)
        self.assertEqual(donation.status, DonationStatus.ACCEPTED)

    # 12. Other pending requests are rejected after acceptance
    def test_12_other_pending_requests_rejected_after_acceptance(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Banquet Food",
            quantity=100,
            unit="meals",
            servings=100,
            expiry_at=timezone.now() + timedelta(hours=8),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.REQUESTED,
        )
        req1 = DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=50,
        )
        req2 = DonationRequest.objects.create(
            donation=donation,
            receiver=self.other_ngo,
            requested_servings=50,
        )

        # Donor accepts req1
        self.client.force_authenticate(user=self.donor)
        accept_url = reverse("donation-request-accept", kwargs={"pk": req1.pk})
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        req1.refresh_from_db()
        req2.refresh_from_db()
        self.assertEqual(req1.status, DonationRequest.RequestStatus.ACCEPTED)
        self.assertEqual(req2.status, DonationRequest.RequestStatus.REJECTED)

    # 13. Invalid lifecycle transition is rejected
    def test_13_invalid_lifecycle_transition_raises_error(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Fresh Salads",
            quantity=20,
            unit="meals",
            servings=20,
            expiry_at=timezone.now() + timedelta(hours=6),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
        )
        # Attempt illegal jump: AVAILABLE directly to COMPLETED
        with self.assertRaises(ValidationError):
            donation.transition_to(DonationStatus.COMPLETED)

    # 14. Unauthorized status modification is rejected
    def test_14_unauthorized_status_modification_rejected(self):
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Hot Stew",
            quantity=20,
            unit="meals",
            servings=20,
            expiry_at=timezone.now() + timedelta(hours=6),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.AVAILABLE,
        )
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-detail", kwargs={"pk": donation.pk})
        # Attempt to set status to COMPLETED via PATCH
        response = self.client.patch(url, {"status": "COMPLETED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        # Status must NOT have changed because status is read-only
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)

    # 15. Donation cancellation rules work correctly
    def test_15_donation_cancellation_rules(self):
        # A. Donor cancels AVAILABLE donation
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.category,
            title="Donation to Cancel",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() + timedelta(hours=4),
            pickup_address="123 St",
            pickup_contact_phone="9876543210",
            status=DonationStatus.AVAILABLE,
        )
        req = DonationRequest.objects.create(
            donation=donation,
            receiver=self.ngo,
            requested_servings=10,
        )
        self.client.force_authenticate(user=self.donor)
        cancel_url = reverse("donation-cancel", kwargs={"pk": donation.pk})
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        donation.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.CANCELLED)
        self.assertEqual(req.status, DonationRequest.RequestStatus.CANCELLED)

        # B. Cannot cancel COMPLETED donation
        donation.status = DonationStatus.COMPLETED
        donation.save(update_fields=["status"])
        response2 = self.client.post(cancel_url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


class FoodCategoryAndOtherFoodItemTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.donor = User.objects.create_user(
            email="chef_other@kitchen.com",
            password="StrongPassword123!",
            first_name="Pastry",
            last_name="Chef",
            role=UserRole.DONOR,
            is_verified=True,
        )

        self.admin = User.objects.create_superuser(
            email="admin_cat@foodshare.org",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
        )

        self.normal_category, _ = FoodCategory.objects.get_or_create(
            slug="cooked-meals",
            defaults={"name": "Cooked Meals", "icon": "🍲", "is_active": True},
        )

        self.other_category, _ = FoodCategory.objects.get_or_create(
            slug="other",
            defaults={"name": "Other", "icon": "📦", "is_active": True},
        )

    # Positive 1: Select Other + enter valid food item -> donation succeeds
    def test_positive_01_other_category_with_valid_food_item_succeeds(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.other_category.id,
            "other_food_item": "Assorted Granola Bars",
            "title": "Fresh Snack Bars Box",
            "quantity": 25,
            "unit": "packets",
            "servings": 25,
            "expiry_at": (timezone.now() + timedelta(days=2)).isoformat(),
            "pickup_address": "45 Market Street",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["other_food_item"], "Assorted Granola Bars")

    # Positive 2: Other + "Homemade Sweets" -> saved and displayed correctly
    def test_positive_02_other_with_homemade_sweets_saved_and_displayed(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.other_category.id,
            "other_food_item": "Homemade Sweets",
            "title": "Festival Sweets Box",
            "quantity": 10,
            "unit": "kg",
            "servings": 40,
            "expiry_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_address": "12 Sweet Lane",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        donation_id = res.data["id"]

        # Check retrieval / display
        detail_url = reverse("donation-detail", kwargs={"pk": donation_id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["other_food_item"], "Homemade Sweets")
        self.assertEqual(detail_res.data["category_details"]["name"], "Other")

    # Positive 3: Normal category + no other_food_item -> donation succeeds
    def test_positive_03_normal_category_no_other_food_item_succeeds(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.normal_category.id,
            "title": "Veg Fried Rice",
            "quantity": 30,
            "unit": "meals",
            "servings": 30,
            "expiry_at": (timezone.now() + timedelta(hours=6)).isoformat(),
            "pickup_address": "88 Central Ave",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res.data["other_food_item"])

    # Positive 4: Change Other -> normal category -> other_food_item is cleared
    def test_positive_04_change_other_to_normal_category_clears_other_food_item(self):
        self.client.force_authenticate(user=self.donor)
        donation = FoodDonation.objects.create(
            donor=self.donor,
            category=self.other_category,
            other_food_item="Homemade Sweets",
            title="Sweets Pack",
            quantity=5,
            unit="kg",
            servings=20,
            expiry_at=timezone.now() + timedelta(days=1),
            pickup_address="12 Sweet Lane",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        self.assertEqual(donation.other_food_item, "Homemade Sweets")

        detail_url = reverse("donation-detail", kwargs={"pk": donation.pk})
        patch_res = self.client.patch(
            detail_url,
            {"category": self.normal_category.id},
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        donation.refresh_from_db()
        self.assertEqual(donation.category, self.normal_category)
        self.assertIsNone(donation.other_food_item)

    # Negative 1: Other + empty food item -> rejected
    def test_negative_01_other_empty_food_item_rejected(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.other_category.id,
            "other_food_item": "",
            "title": "Unspecified Surplus",
            "quantity": 10,
            "unit": "meals",
            "servings": 10,
            "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
            "pickup_address": "123 Test St",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("other_food_item", res.data)

    # Negative 2: Other + whitespace-only food item -> rejected
    def test_negative_02_other_whitespace_only_food_item_rejected(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.other_category.id,
            "other_food_item": "     ",
            "title": "Whitespace Surplus",
            "quantity": 10,
            "unit": "meals",
            "servings": 10,
            "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
            "pickup_address": "123 Test St",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("other_food_item", res.data)

    # Negative 3: Other + food item exceeding maximum length -> rejected
    def test_negative_03_other_food_item_exceeding_max_length_rejected(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.other_category.id,
            "other_food_item": "X" * 101,
            "title": "Overly Long Description",
            "quantity": 10,
            "unit": "meals",
            "servings": 10,
            "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
            "pickup_address": "123 Test St",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("other_food_item", res.data)

    # Negative 4: Invalid category -> rejected
    def test_negative_04_invalid_category_rejected(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": 999999,
            "title": "Invalid Category Test",
            "quantity": 10,
            "unit": "meals",
            "servings": 10,
            "expiry_at": (timezone.now() + timedelta(hours=4)).isoformat(),
            "pickup_address": "123 Test St",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", res.data)

    # Negative 5: Verify existing normal-category donations still work
    def test_negative_05_existing_normal_category_donations_work(self):
        self.client.force_authenticate(user=self.donor)
        url = reverse("donation-list-create")
        payload = {
            "category": self.normal_category.id,
            "title": "Standard Dal Roti",
            "quantity": 20,
            "unit": "meals",
            "servings": 20,
            "expiry_at": (timezone.now() + timedelta(hours=5)).isoformat(),
            "pickup_address": "123 Normal St",
            "pickup_city": "Delhi",
            "pickup_contact_phone": "9876543210",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["category"], self.normal_category.id)
        self.assertIsNone(res.data["other_food_item"])

    # Category filtering via API
    def test_category_filter_via_api(self):
        # Create one in normal and one in other
        FoodDonation.objects.create(
            donor=self.donor,
            category=self.normal_category,
            title="Cooked Meal Item",
            quantity=10,
            unit="meals",
            servings=10,
            expiry_at=timezone.now() + timedelta(days=1),
            pickup_address="123 St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )
        FoodDonation.objects.create(
            donor=self.donor,
            category=self.other_category,
            other_food_item="Homemade Sweets",
            title="Other Item",
            quantity=5,
            unit="kg",
            servings=15,
            expiry_at=timezone.now() + timedelta(days=1),
            pickup_address="123 St",
            pickup_city="Delhi",
            pickup_contact_phone="9876543210",
        )

        url = reverse("donation-list-create")
        res_normal = self.client.get(f"{url}?category={self.normal_category.id}")
        self.assertEqual(res_normal.status_code, status.HTTP_200_OK)
        items_normal = res_normal.data if isinstance(res_normal.data, list) else res_normal.data.get("results", [])
        self.assertTrue(all(d["category"] == self.normal_category.id for d in items_normal))

        res_other = self.client.get(f"{url}?category={self.other_category.id}")
        self.assertEqual(res_other.status_code, status.HTTP_200_OK)
        items_other = res_other.data if isinstance(res_other.data, list) else res_other.data.get("results", [])
        self.assertTrue(all(d["category"] == self.other_category.id for d in items_other))


"""
FoodShare — Automated End-to-End Verification of the Primary FoodShare Workflow.

Validates the full multi-role operational lifecycle:
1. DONOR registers and logs in via JWT.
2. DONOR posts an active surplus food donation.
3. NGO registers, logs in via JWT, browses available donations, and submits a claim request.
4. DONOR reviews incoming claim requests and accepts the NGO request.
5. SYSTEM automatically generates a Pickup ticket with PENDING status.
6. VOLUNTEER registers, logs in via JWT, queries available pickups, and claims the task.
7. VOLUNTEER executes physical collection: marks food as PICKED_UP.
8. VOLUNTEER executes physical delivery: marks food as DELIVERED to NGO.
9. VOLUNTEER completes the delivery: marks task as COMPLETED.
10. Final state assertion:
    - FoodDonation status == COMPLETED
    - DonationRequest status == ACCEPTED
    - Pickup status == COMPLETED
    - Volunteer profile deliveries_completed == 1
"""
import os
import sys
import uuid
import re
from datetime import timedelta
from typing import Any

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ.setdefault("USE_SQLITE", "True")

import django
django.setup()

from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User, UserRole, NGOProfile, VolunteerProfile, EmailOTP
from apps.donations.models import FoodCategory, FoodDonation, DonationRequest, DonationStatus
from apps.pickups.models import Pickup, PickupStatus


class FoodShareWorkflowEndToEndTests(TestCase):
    """
    Automated end-to-end verification of the primary FoodShare workflow.
    Uses dynamic unique test identities per execution.
    No ADMIN user created.
    """

    client: Any
    category: Any

    def setUp(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.client = APIClient()
        self.uid = uuid.uuid4().hex[:8]
        self.donor_email = f"e2e-donor-{self.uid}@foodshare.test"
        self.ngo_email = f"e2e-ngo-{self.uid}@foodshare.test"
        self.volunteer_email = f"e2e-volunteer-{self.uid}@foodshare.test"
        self.test_password = "StrongPassword123!"

        self.category, _ = FoodCategory.objects.get_or_create(
            slug=f"e2e-meals-{self.uid}",
            defaults={"name": f"E2E Meals {self.uid}", "description": "Prepared hot meals", "is_active": True},
        )
        seed = int(self.uid, 16) % 1000000
        self.donor_phone = f"91{seed:06d}01"[:10]
        self.ngo_phone = f"92{seed:06d}02"[:10]
        self.volunteer_phone = f"93{seed:06d}03"[:10]

    def _perform_two_step_login(self, email: str, password: str) -> str:
        """Helper to perform Step 1 (credential check & OTP dispatch) and Step 2 (OTP verification & token receipt)."""
        login_res = self.client.post("/api/v1/auth/token/", {
            "email": email,
            "password": password,
        }, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertTrue(login_res.data.get("login_otp_required"))
        self.assertNotIn("access", login_res.data)

        from django.core import mail
        code = None
        if hasattr(mail, "outbox") and mail.outbox:
            body_text = str(mail.outbox[-1].body)
            match = re.search(r"code is:\s*(\d{6})", body_text)
            if match:
                code = match.group(1)

        if not code:
            user = User.objects.get(email=email)
            _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)

        verify_res = self.client.post("/api/v1/auth/login-otp/verify/", {
            "email": email,
            "otp": code,
        }, format="json")
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_res.data)
        return str(verify_res.data["access"])

    def test_complete_primary_foodshare_workflow(self):
        # ------------------------------------------------------------------
        # Step 1: Donor Registration & Login
        # ------------------------------------------------------------------
        reg_res = self.client.post("/api/v1/users/register/", {
            "email": self.donor_email,
            "password": self.test_password,
            "password_confirm": self.test_password,
            "first_name": "Bistro",
            "last_name": "Chef",
            "phone_number": self.donor_phone,
            "role": UserRole.DONOR,
            "organization_name": "Green Bistro Kitchen",
        }, format="json")
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)

        # Mark email verified for Donor to enable JWT login (Phase B requirement)
        donor_user = User.objects.get(email=self.donor_email)
        donor_user.is_verified = True
        donor_user.save()

        donor_token = self._perform_two_step_login(self.donor_email, self.test_password)

        # ------------------------------------------------------------------
        # Step 2: Donor Posts Surplus Food Donation
        # ------------------------------------------------------------------
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {donor_token}")
        expiry = timezone.now() + timedelta(hours=12)
        post_res = self.client.post("/api/v1/donations/", {
            "title": f"Surplus Dal & Basmati Rice Batch {self.uid}",
            "category": self.category.id,
            "dietary_type": "VEG",
            "quantity": 40,
            "unit": "meals",
            "servings": 40,
            "expiry_at": expiry.isoformat(),
            "pickup_address": "12 Connaught Circle",
            "pickup_city": "Delhi NCR",
            "pickup_contact_phone": "9810012345",
            "special_instructions": "Keep in warm containers.",
        }, format="json")
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        donation_id = post_res.data["id"]
        donation: Any = FoodDonation.objects.get(pk=donation_id)
        self.assertEqual(donation.status, DonationStatus.AVAILABLE)

        # ------------------------------------------------------------------
        # Step 3: NGO Registration, Verification & Login
        # ------------------------------------------------------------------
        self.client.credentials()  # Clear auth
        ngo_reg = self.client.post("/api/v1/users/register/", {
            "email": self.ngo_email,
            "password": self.test_password,
            "password_confirm": self.test_password,
            "first_name": "Hope",
            "last_name": "Shelter",
            "phone_number": self.ngo_phone,
            "role": UserRole.NGO_RECEIVER,
            "organization_name": "City Hope Shelter",
        }, format="json")
        self.assertEqual(ngo_reg.status_code, status.HTTP_201_CREATED)
        ngo_user = User.objects.get(email=self.ngo_email)

        # Mark email verified & NGO profile verified so NGO has authorization to claim
        ngo_user.is_verified = True
        ngo_user.save()
        ngo_profile, _ = NGOProfile.objects.get_or_create(user=ngo_user)
        ngo_profile.is_verified = True
        ngo_profile.save()

        ngo_token = self._perform_two_step_login(self.ngo_email, self.test_password)

        # ------------------------------------------------------------------
        # Step 4: NGO Browses Available Surplus and Submits Claim Request
        # ------------------------------------------------------------------
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {ngo_token}")
        browse_res = self.client.get("/api/v1/donations/")
        self.assertEqual(browse_res.status_code, status.HTTP_200_OK)
        donation_ids = [d["id"] for d in (browse_res.data.get("results", browse_res.data))]
        self.assertIn(donation_id, donation_ids)

        claim_res = self.client.post("/api/v1/donations/requests/", {
            "donation": donation_id,
            "requested_servings": 40,
            "message": "Distribution at City Shelter evening meal program.",
        }, format="json")
        self.assertEqual(claim_res.status_code, status.HTTP_201_CREATED)
        claim_id = claim_res.data["id"]
        claim_req: Any = DonationRequest.objects.get(pk=claim_id)
        self.assertEqual(claim_req.status, DonationRequest.RequestStatus.PENDING)
        donation.refresh_from_db()
        self.assertEqual(donation.status, DonationStatus.REQUESTED)

        # ------------------------------------------------------------------
        # Step 5: Donor Reviews and Accepts Claim Request
        # ------------------------------------------------------------------
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {donor_token}")
        accept_res = self.client.post(f"/api/v1/donations/requests/{claim_id}/accept/")
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)
        claim_req.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(claim_req.status, DonationRequest.RequestStatus.ACCEPTED)
        self.assertEqual(donation.status, DonationStatus.ACCEPTED)

        # ------------------------------------------------------------------
        # Step 6: System Automatically Creates Pickup Record
        # ------------------------------------------------------------------
        pickup_record = Pickup.objects.filter(donation=donation).first()
        self.assertIsNotNone(pickup_record)
        assert pickup_record is not None
        pickup: Any = pickup_record
        self.assertEqual(pickup.status, PickupStatus.PENDING)
        self.assertIsNone(pickup.volunteer)

        # ------------------------------------------------------------------
        # Step 7: Volunteer Registration, Login & Claim
        # ------------------------------------------------------------------
        self.client.credentials()  # Clear auth
        vol_reg = self.client.post("/api/v1/users/register/", {
            "email": self.volunteer_email,
            "password": self.test_password,
            "password_confirm": self.test_password,
            "first_name": "Ravi",
            "last_name": "Kumar",
            "phone_number": self.volunteer_phone,
            "role": UserRole.VOLUNTEER,
        }, format="json")
        self.assertEqual(vol_reg.status_code, status.HTTP_201_CREATED)
        volunteer_user = User.objects.get(email=self.volunteer_email)

        # Mark email verified for Volunteer to enable JWT login (Phase B requirement)
        volunteer_user.is_verified = True
        volunteer_user.save()

        vol_token = self._perform_two_step_login(self.volunteer_email, self.test_password)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {vol_token}")
        avail_res = self.client.get("/api/v1/pickups/available/")
        self.assertEqual(avail_res.status_code, status.HTTP_200_OK)
        avail_ids = [p["id"] for p in (avail_res.data.get("results", avail_res.data))]
        self.assertIn(pickup.id, avail_ids)

        claim_pickup_res = self.client.post(f"/api/v1/pickups/{pickup.id}/assign/")
        self.assertEqual(claim_pickup_res.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.ASSIGNED)
        self.assertEqual(pickup.volunteer, volunteer_user)
        self.assertEqual(donation.status, DonationStatus.PICKUP_ASSIGNED)

        # ------------------------------------------------------------------
        # Step 8: Volunteer Marks Food Picked Up
        # ------------------------------------------------------------------
        pu_res = self.client.post(f"/api/v1/pickups/{pickup.id}/pickup/")
        self.assertEqual(pu_res.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.PICKED_UP)
        self.assertIsNotNone(pickup.picked_up_at)
        self.assertEqual(donation.status, DonationStatus.PICKED_UP)

        # ------------------------------------------------------------------
        # Step 9: Volunteer Marks Food Delivered
        # ------------------------------------------------------------------
        del_res = self.client.post(f"/api/v1/pickups/{pickup.id}/deliver/")
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(pickup.status, PickupStatus.DELIVERED)
        self.assertIsNotNone(pickup.delivered_at)
        self.assertEqual(donation.status, DonationStatus.DELIVERED)

        # ------------------------------------------------------------------
        # Step 10: Volunteer Completes Delivery Task
        # ------------------------------------------------------------------
        comp_res = self.client.post(f"/api/v1/pickups/{pickup.id}/complete/")
        self.assertEqual(comp_res.status_code, status.HTTP_200_OK)
        pickup.refresh_from_db()
        donation.refresh_from_db()
        vol_profile: Any = VolunteerProfile.objects.get(user=volunteer_user)
        self.assertEqual(pickup.status, PickupStatus.COMPLETED)
        self.assertEqual(donation.status, DonationStatus.COMPLETED)
        self.assertEqual(vol_profile.deliveries_completed, 1)

        # ------------------------------------------------------------------
        # Step 11: Final State Audit
        # ------------------------------------------------------------------
        self.assertEqual(donation.status, DonationStatus.COMPLETED)
        self.assertEqual(claim_req.status, DonationRequest.RequestStatus.ACCEPTED)
        self.assertEqual(pickup.status, PickupStatus.COMPLETED)
        self.assertEqual(vol_profile.deliveries_completed, 1)


if __name__ == "__main__":
    from django.core.management import call_command
    call_command("test", "tests_e2e_workflow")


"""
FoodShare — Users & Authentication Test Suite.

Verifies:
1. Donor registration
2. NGO registration
3. Volunteer registration
4. Admin self-registration rejection
5. Duplicate email rejection
6. Login with valid credentials
7. Login with invalid credentials
8. Authenticated profile retrieval
9. Role isolation & permission checks (self-promotion block, verified vs unverified NGO)
10. Password hashing verification & security sanitization (no plaintext, hashes unexposed)
"""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.users.models import (
    User,
    UserRole,
    DonorProfile,
    NGOProfile,
    VolunteerProfile,
    EmailOTP,
)
from apps.users.permissions import (
    IsPlatformAdmin,
    IsDonor,
    IsNGOReceiver,
    IsVerifiedNGO,
    IsVolunteer,
)


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()

    def _extract_latest_otp_code(self):
        import re
        from django.core import mail
        if mail.outbox:
            body_text = str(mail.outbox[-1].body)
            match = re.search(r"code is:\s*(\d{6})", body_text)
            if match:
                return match.group(1)
        return None

    # 1. Donor registration
    def test_01_donor_registration_success(self):
        url = reverse("user-register")
        payload = {
            "email": "donor@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Fresh",
            "last_name": "Bites",
            "phone_number": "9876543210",
            "role": "donor",
            "organization_name": "Fresh Bites Cafe",
            "donor_type": "restaurant",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Phase B: Public registration does not grant JWT tokens directly
        self.assertNotIn("tokens", response.data)
        self.assertIn("user", response.data)

        user = User.objects.get(email="donor@example.com")
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_donor)
        self.assertEqual(user.role, UserRole.DONOR)
        self.assertEqual(user.donor_profile.organization_name, "Fresh Bites Cafe")
        self.assertEqual(user.donor_profile.donor_type, DonorProfile.DonorType.RESTAURANT)

    # 2. NGO registration
    def test_02_ngo_registration_success(self):
        url = reverse("user-register")
        payload = {
            "email": "hope@ngo.org",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Hope",
            "last_name": "Foundation",
            "phone_number": "9123456780",
            "role": "ngo_receiver",
            "organization_name": "Hope Shelter",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="hope@ngo.org")
        self.assertTrue(user.is_ngo)
        self.assertEqual(user.role, UserRole.NGO_RECEIVER)
        self.assertEqual(user.ngo_profile.organization_name, "Hope Shelter")
        # Newly registered NGOs must default to unverified
        self.assertFalse(user.ngo_profile.is_verified)

    # 3. Volunteer registration
    def test_03_volunteer_registration_success(self):
        url = reverse("user-register")
        payload = {
            "email": "volunteer@ride.org",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Sam",
            "last_name": "Rider",
            "phone_number": "9988776655",
            "role": "volunteer",
            "vehicle_type": "bicycle",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="volunteer@ride.org")
        self.assertTrue(user.is_volunteer)
        self.assertEqual(user.role, UserRole.VOLUNTEER)
        self.assertEqual(user.volunteer_profile.vehicle_type, VolunteerProfile.VehicleType.BICYCLE)
        self.assertTrue(user.volunteer_profile.is_available)
        self.assertEqual(user.volunteer_profile.deliveries_completed, 0)

    # 4. Admin self-registration rejection
    def test_04_admin_self_registration_disallowed(self):
        url = reverse("user-register")
        payload = {
            "email": "hacker@evil.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "role": "admin",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="hacker@evil.com").exists())

    # 5. Duplicate email rejection
    def test_05_duplicate_email_rejected(self):
        User.objects.create_user(
            email="existing@example.com",
            password="ExistingPassword123!",
            role=UserRole.DONOR,
            phone_number="9876543210",
        )
        url = reverse("user-register")
        payload = {
            "email": "existing@example.com",
            "password": "NewPassword123!",
            "password_confirm": "NewPassword123!",
            "first_name": "Jane",
            "phone_number": "9876543211",
            "role": "donor",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("An account with this email already exists.", str(response.data["email"]))

    # 6. Login with valid credentials (two-step login flow)
    def test_06_login_with_valid_credentials(self):
        user = User.objects.create_user(
            email="validuser@example.com",
            password="CorrectPassword123!",
            role=UserRole.DONOR,
        )
        url = reverse("token-obtain-pair")
        payload = {
            "email": "validuser@example.com",
            "password": "CorrectPassword123!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Step 1 asserts: login_otp_required is True, no access/refresh JWT tokens
        self.assertTrue(response.data.get("login_otp_required"))
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

        # Step 2: Complete login with Login OTP
        code = self._extract_latest_otp_code()
        self.assertIsNotNone(code)
        verify_url = reverse("user-login-otp-verify")
        verify_res = self.client.post(verify_url, {"email": "validuser@example.com", "otp": code})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_res.data)
        self.assertIn("refresh", verify_res.data)

    # 7. Login with invalid credentials
    def test_07_login_with_invalid_credentials(self):
        user = User.objects.create_user(
            email="validuser2@example.com",
            password="CorrectPassword123!",
            role=UserRole.DONOR,
        )
        url = reverse("token-obtain-pair")

        # Wrong password
        response = self.client.post(url, {
            "email": "validuser2@example.com",
            "password": "WrongPassword999!",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Security: No Login OTP generated on wrong password
        self.assertFalse(EmailOTP.objects.filter(user=user, purpose=EmailOTP.OTPPurpose.LOGIN).exists())

        # Non-existent user
        response = self.client.post(url, {
            "email": "ghost@example.com",
            "password": "AnyPassword123!",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 8. Authenticated profile retrieval
    def test_08_authenticated_profile_retrieval(self):
        user = User.objects.create_user(
            email="profiletest@example.com",
            password="StrongPassword123!",
            first_name="Alice",
            last_name="Green",
            role=UserRole.DONOR,
        )
        DonorProfile.objects.create(
            user=user,
            organization_name="Green Harvest",
            donor_type=DonorProfile.DonorType.HOTEL,
        )
        url = reverse("user-me")

        # Unauthenticated request returns 401
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated request returns 200 with full profile
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profiletest@example.com")
        self.assertEqual(response.data["role"], "donor")
        self.assertIsNotNone(response.data["donor_profile"])
        self.assertEqual(response.data["donor_profile"]["organization_name"], "Green Harvest")

    # 9. Role isolation & permission checks
    def test_09_role_isolation_and_permissions(self):
        # A. Attempt self-promotion via profile update API
        donor = User.objects.create_user(
            email="regular_donor@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
        )
        self.client.force_authenticate(user=donor)
        update_url = reverse("user-me")
        response = self.client.patch(update_url, {"role": "admin", "first_name": "Promoted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        donor.refresh_from_db()
        self.assertEqual(donor.role, UserRole.DONOR, "User must NOT be able to self-promote to ADMIN!")
        self.assertEqual(donor.first_name, "Promoted")

        # B. Permission class verification
        ngo = User.objects.create_user(
            email="unverified@ngo.org",
            password="StrongPassword123!",
            role=UserRole.NGO_RECEIVER,
        )
        ngo_prof = NGOProfile.objects.create(user=ngo, organization_name="Unverified Shelter", is_verified=False)

        admin = User.objects.create_superuser(
            email="admin@foodshare.org",
            password="AdminPassword123!",
        )

        request = self.factory.get("/dummy/")

        # Unverified NGO: IsNGOReceiver passes, but IsVerifiedNGO fails
        request.user = ngo
        self.assertTrue(IsNGOReceiver().has_permission(request, None))
        self.assertFalse(IsVerifiedNGO().has_permission(request, None))
        self.assertFalse(IsPlatformAdmin().has_permission(request, None))
        self.assertFalse(IsVolunteer().has_permission(request, None))

        # Admin: passes IsPlatformAdmin and IsVerifiedNGO
        request.user = admin
        self.assertTrue(IsPlatformAdmin().has_permission(request, None))
        self.assertTrue(IsVerifiedNGO().has_permission(request, None))

        # Once NGO is verified by admin: IsVerifiedNGO passes
        ngo_prof.is_verified = True
        ngo_prof.save()
        request.user = ngo
        self.assertTrue(IsVerifiedNGO().has_permission(request, None))

    # 10. Password hashing verification & security sanitization
    def test_10_password_hashing_and_security(self):
        raw_password = "SuperSecretPassword123!"
        user = User.objects.create_user(
            email="security_test@example.com",
            password=raw_password,
            role=UserRole.DONOR,
        )

        # A. Assert password is NOT stored in plaintext
        self.assertNotEqual(user.password, raw_password)
        self.assertTrue(
            user.password.startswith("pbkdf2_sha256$") or user.password.startswith("argon2"),
            "Password must be securely hashed.",
        )
        self.assertTrue(user.check_password(raw_password))

        # B. Assert registration API does not leak password hash
        reg_url = reverse("user-register")
        reg_response = self.client.post(reg_url, {
            "email": "leaktst@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Leak",
            "phone_number": "9811223344",
            "role": "donor",
        })
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", reg_response.data["user"])
        self.assertNotIn("password_hash", reg_response.data["user"])

        # C. Assert profile API does not leak password hash
        self.client.force_authenticate(user=user)
        profile_response = self.client.get(reverse("user-me"))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", profile_response.data)
        self.assertNotIn("password_hash", profile_response.data)

    # 11. UserManager create_user and create_superuser validation
    def test_11_user_manager_methods(self):
        # Empty email raises ValueError
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="password123")

        # create_superuser creates staff, superuser, and admin role
        super_u = User.objects.create_superuser(
            email="root@foodshare.org",
            password="RootPassword123!",
        )
        self.assertTrue(super_u.is_staff)
        self.assertTrue(super_u.is_superuser)
        self.assertTrue(super_u.is_admin_user)
        self.assertEqual(super_u.role, UserRole.ADMIN)

        # Superuser with is_staff=False or is_superuser=False raises ValueError
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="badstaff@foodshare.org",
                password="password123",
                is_staff=False,
            )
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="badsuper@foodshare.org",
                password="password123",
                is_superuser=False,
            )

    # 12. Case-insensitive duplicate email rejection
    def test_12_case_insensitive_email_duplicate_rejected(self):
        User.objects.create_user(
            email="donor.case@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9870000001",
        )
        url = reverse("user-register")
        payload = {
            "email": "DONOR.CASE@EXAMPLE.COM",
            "password": "NewPassword123!",
            "password_confirm": "NewPassword123!",
            "first_name": "Test",
            "phone_number": "9870000002",
            "role": "donor",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("An account with this email already exists.", str(response.data.get("email", "")))

    # 13. Duplicate mobile number rejected across roles
    def test_13_duplicate_phone_number_across_roles_rejected(self):
        User.objects.create_user(
            email="firstuser@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9876543210",
        )
        url = reverse("user-register")
        payload = {
            "email": "seconduser@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Volunteer",
            "phone_number": "9876543210",
            "role": "volunteer",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("An account with this mobile number already exists.", str(response.data.get("phone_number", "")))

    # 14. Mobile number format validation
    def test_14_mobile_number_format_validation(self):
        url = reverse("user-register")
        invalid_phones = [
            "98765abcde",  # Letters
            "98765",       # Less than 10 digits
            "98765432100", # More than 10 digits
            "98765-4321",  # Hyphens / special symbols
            "+9198765432", # Country code / symbols
            "",            # Empty
        ]
        for bad_phone in invalid_phones:
            payload = {
                "email": f"badphone_{abs(hash(bad_phone))}@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": "BadPhone",
                "phone_number": bad_phone,
                "role": "donor",
            }
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Mobile number must contain exactly 10 digits.", str(response.data.get("phone_number", "")))

    # 15. First name validation
    def test_15_first_name_validation(self):
        url = reverse("user-register")
        invalid_names = [
            "John2",     # Digits
            "John@Doe",  # Symbols
            "12345",     # Numbers
            "   ",       # Whitespace only
        ]
        for bad_name in invalid_names:
            payload = {
                "email": f"badname_{abs(hash(bad_name))}@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": bad_name,
                "phone_number": "9812345670",
                "role": "donor",
            }
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("Please enter a valid name.", str(response.data.get("first_name", "")))

        # Valid names with hyphens, apostrophes, and spaces are accepted
        valid_payload = {
            "email": "mary.jane@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Mary-Jane",
            "last_name": "O'Connor",
            "phone_number": "9812345671",
            "role": "donor",
        }
        res = self.client.post(url, valid_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # 16. Last name format validation
    def test_16_last_name_format_validation(self):
        url = reverse("user-register")
        payload = {
            "email": "badlastname@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "ValidName",
            "last_name": "Smith123",
            "phone_number": "9812345672",
            "role": "donor",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please enter a valid name.", str(response.data.get("last_name", "")))

    # 17. Password validation (mismatch and length)
    def test_17_password_validation(self):
        url = reverse("user-register")
        # Password mismatch
        mismatch_payload = {
            "email": "mismatch@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
            "first_name": "Alice",
            "phone_number": "9812345673",
            "role": "donor",
        }
        res = self.client.post(url, mismatch_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match.", str(res.data))

        # Too short (< 8 chars)
        short_payload = {
            "email": "shortpw@example.com",
            "password": "short",
            "password_confirm": "short",
            "first_name": "Alice",
            "phone_number": "9812345674",
            "role": "donor",
        }
        res = self.client.post(url, short_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    # 18. Role-specific validation (NGO organization name required)
    def test_18_role_specific_ngo_organization_required(self):
        url = reverse("user-register")
        payload = {
            "email": "noorgngo@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Shelter",
            "phone_number": "9812345675",
            "role": "ngo_receiver",
            "organization_name": "",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Organization name is required for NGOs.", str(response.data.get("organization_name", "")))

    # 19. Automatic EmailOTP creation on registration
    def test_19_automatic_email_otp_creation_on_registration(self):
        url = reverse("user-register")
        payload = {
            "email": "otptest@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "OtpUser",
            "phone_number": "9812345676",
            "role": "donor",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="otptest@example.com")
        otp = EmailOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(otp)
        self.assertEqual(otp.attempts, 0)
        self.assertFalse(otp.is_expired())

    # 20. EmailOTP verification and resend endpoints
    def test_20_email_otp_verification_and_resend_endpoints(self):
        user = User.objects.create_user(
            email="otpflow@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345677",
            is_verified=False,
        )
        otp_obj, code = EmailOTP.create_otp(user)
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)

        verify_url = reverse("user-verify-otp")
        resend_url = reverse("user-resend-otp")

        # Wrong code
        bad_res = self.client.post(verify_url, {"email": user.email, "otp": "000000"})
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)
        otp_obj.refresh_from_db()
        self.assertEqual(otp_obj.attempts, 1)

        # Resend OTP while unverified succeeds and generates new code
        resend_res = self.client.post(resend_url, {"email": user.email})
        self.assertEqual(resend_res.status_code, status.HTTP_200_OK)
        self.assertEqual(resend_res.data.get("message"), "New verification code sent.")

        # Prior OTP should now be marked used/invalidated
        otp_obj.refresh_from_db()
        self.assertTrue(otp_obj.is_used)

        # New OTP should exist
        new_otp = EmailOTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(new_otp)
        self.assertNotEqual(new_otp.id, otp_obj.id)

        # Max attempts lockout on new OTP (5 failed attempts)
        for _ in range(5):
            self.client.post(verify_url, {"email": user.email, "otp": "999999"})
        new_otp.refresh_from_db()
        self.assertTrue(new_otp.is_used)

    # 21. Unverified account login rejection (HTTP 401)
    def test_21_unverified_account_login_rejected(self):
        user = User.objects.create_user(
            email="unverified@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345681",
            is_verified=False,
        )
        url = reverse("token-obtain-pair")
        payload = {
            "email": "unverified@example.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Please verify your email before continuing.", str(response.data.get("detail", "")))
        # Security: No Login OTP generated for unverified account
        self.assertFalse(EmailOTP.objects.filter(user=user, purpose=EmailOTP.OTPPurpose.LOGIN).exists())

    # 22. Verified account login succeeds (HTTP 200 with two-step Login OTP)
    def test_22_verified_account_login_succeeds(self):
        user = User.objects.create_user(
            email="verified@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345682",
            is_verified=True,
        )
        url = reverse("token-obtain-pair")
        payload = {
            "email": "verified@example.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("login_otp_required"))
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

        # Step 2: Complete login with Login OTP
        code = self._extract_latest_otp_code()
        self.assertIsNotNone(code)
        verify_url = reverse("user-login-otp-verify")
        verify_res = self.client.post(verify_url, {"email": "verified@example.com", "otp": code})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_res.data)
        self.assertIn("refresh", verify_res.data)

    # 23. Public registration creates unverified user and issues no tokens
    def test_23_public_registration_creates_unverified_user_no_tokens(self):
        url = reverse("user-register")
        payload = {
            "email": "unverified.donor@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Public",
            "last_name": "Donor",
            "phone_number": "9812345683",
            "role": "donor",
            "donor_type": "individual",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("tokens", res.data)

        user = User.objects.get(email="unverified.donor@example.com")
        self.assertFalse(user.is_verified)

    # 24. OTP verification marks user verified and issues JWT tokens
    def test_24_otp_verification_marks_verified_and_issues_tokens(self):
        user = User.objects.create_user(
            email="toverify@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345684",
            is_verified=False,
        )
        _, code = EmailOTP.create_otp(user)
        verify_url = reverse("user-verify-otp")
        res = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", res.data)
        self.assertIn("access", res.data["tokens"])
        self.assertIn("refresh", res.data["tokens"])
        self.assertIn("user", res.data)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    # 25. Reused OTP rejected
    def test_25_reused_otp_rejected(self):
        user = User.objects.create_user(
            email="reusedotp@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345685",
            is_verified=False,
        )
        _, code = EmailOTP.create_otp(user)
        verify_url = reverse("user-verify-otp")

        # First use succeeds
        res1 = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Second use fails
        res2 = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    # 26. Resend invalidates prior OTP
    def test_26_resend_invalidates_prior_otp(self):
        user = User.objects.create_user(
            email="invalidation@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345686",
            is_verified=False,
        )
        _, code1 = EmailOTP.create_otp(user)
        resend_url = reverse("user-resend-otp")
        resend_res = self.client.post(resend_url, {"email": user.email})
        self.assertEqual(resend_res.status_code, status.HTTP_200_OK)

        verify_url = reverse("user-verify-otp")
        # Old code1 is rejected
        res_old = self.client.post(verify_url, {"email": user.email, "otp": code1})
        self.assertEqual(res_old.status_code, status.HTTP_400_BAD_REQUEST)

    # 27. Resend rejected for already verified user
    def test_27_resend_rejected_for_already_verified_user(self):
        user = User.objects.create_user(
            email="alreadyverified@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345687",
            is_verified=True,
        )
        resend_url = reverse("user-resend-otp")
        resend_res = self.client.post(resend_url, {"email": user.email})
        self.assertEqual(resend_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already verified", str(resend_res.data))

    # 28. Password reset request nonexistent email returns 400
    def test_28_password_reset_request_nonexistent_email_returns_400(self):
        url = reverse("password-reset-request")
        res = self.client.post(url, {"email": "nonexistent@example.com"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No account found with this email address.", str(res.data))

    # 29. Password reset request valid email success
    def test_29_password_reset_request_valid_email_success(self):
        user = User.objects.create_user(
            email="resetuser@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345688",
            is_verified=True,
        )
        url = reverse("password-reset-request")
        res = self.client.post(url, {"email": user.email})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("Password reset code sent", res.data.get("message", ""))

        otp = EmailOTP.objects.filter(
            user=user,
            purpose=EmailOTP.OTPPurpose.PASSWORD_RESET,
            is_used=False,
        ).first()
        self.assertIsNotNone(otp)
        self.assertEqual(otp.purpose, EmailOTP.OTPPurpose.PASSWORD_RESET)

    # 30. Password reset confirm success
    def test_30_password_reset_confirm_success(self):
        user = User.objects.create_user(
            email="confirmreset@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345689",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        res = self.client.post(
            url,
            {
                "email": user.email,
                "otp": code,
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("Password reset successfully", res.data.get("message", ""))

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPassword123!"))
        self.assertFalse(user.check_password("OldPassword123!"))

    # 31. Login with new password succeeds and old password fails
    def test_31_login_with_new_password_succeeds_and_old_password_fails(self):
        user = User.objects.create_user(
            email="loginreset@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345690",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        # Reset password
        confirm_url = reverse("password-reset-confirm")
        self.client.post(
            confirm_url,
            {
                "email": user.email,
                "otp": code,
                "new_password": "BrandNewPassword123!",
                "new_password_confirm": "BrandNewPassword123!",
            },
        )

        token_url = reverse("token-obtain-pair")
        # Old password fails
        old_res = self.client.post(token_url, {"email": user.email, "password": "OldPassword123!"})
        self.assertEqual(old_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # New password succeeds (two-step login: step 1 requests OTP, step 2 verifies OTP)
        new_res = self.client.post(token_url, {"email": user.email, "password": "BrandNewPassword123!"})
        self.assertEqual(new_res.status_code, status.HTTP_200_OK)
        self.assertTrue(new_res.data.get("login_otp_required"))
        self.assertNotIn("access", new_res.data)

        # Step 2: Complete login with Login OTP
        login_code = self._extract_latest_otp_code()
        self.assertIsNotNone(login_code)
        verify_login_url = reverse("user-login-otp-verify")
        verify_res = self.client.post(verify_login_url, {"email": user.email, "otp": login_code})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_res.data)
        self.assertIn("refresh", verify_res.data)

    # 32. Password reset confirm invalid OTP countdown
    def test_32_password_reset_confirm_invalid_otp_countdown(self):
        user = User.objects.create_user(
            email="wrongotp@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345691",
            is_verified=True,
        )
        _, _ = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        res = self.client.post(
            url,
            {
                "email": user.email,
                "otp": "000000",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("4 attempts remaining", str(res.data))

    # 33. Password reset confirm lockout after 5 attempts
    def test_33_password_reset_confirm_lockout_after_5_attempts(self):
        user = User.objects.create_user(
            email="lockout@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345692",
            is_verified=True,
        )
        _, valid_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        for i in range(5):
            res = self.client.post(
                url,
                {
                    "email": user.email,
                    "otp": "999999",
                    "new_password": "NewStrongPassword123!",
                    "new_password_confirm": "NewStrongPassword123!",
                },
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # 6th attempt with the CORRECT code should now be rejected because OTP is locked (is_used=True)
        res_correct = self.client.post(
            url,
            {
                "email": user.email,
                "otp": valid_code,
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res_correct.status_code, status.HTTP_400_BAD_REQUEST)

    # 34. Password reset confirm reused OTP fails
    def test_34_password_reset_confirm_reused_otp_fails(self):
        user = User.objects.create_user(
            email="reusedreset@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345693",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        payload = {
            "email": user.email,
            "otp": code,
            "new_password": "NewStrongPassword123!",
            "new_password_confirm": "NewStrongPassword123!",
        }
        res1 = self.client.post(url, payload)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Reusing the same OTP fails
        res2 = self.client.post(url, payload)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    # 35. Password reset resend invalidates old OTP
    def test_35_password_reset_resend_invalidates_old_otp(self):
        user = User.objects.create_user(
            email="resendinvalid@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345694",
            is_verified=True,
        )
        _, old_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        resend_url = reverse("password-reset-resend")
        resend_res = self.client.post(resend_url, {"email": user.email})
        self.assertEqual(resend_res.status_code, status.HTTP_200_OK)

        confirm_url = reverse("password-reset-confirm")
        # Old code is rejected
        res = self.client.post(
            confirm_url,
            {
                "email": user.email,
                "otp": old_code,
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 36. Password reset confirm expired OTP fails
    def test_36_password_reset_confirm_expired_otp_fails(self):
        user = User.objects.create_user(
            email="expiredreset@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345695",
            is_verified=True,
        )
        otp, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)
        from datetime import timedelta
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save(update_fields=["expires_at"])

        url = reverse("password-reset-confirm")
        res = self.client.post(
            url,
            {
                "email": user.email,
                "otp": code,
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(res.data).lower())

    # 37. Password reset confirm passwords mismatch fails
    def test_37_password_reset_confirm_passwords_mismatch_fails(self):
        user = User.objects.create_user(
            email="mismatch@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345696",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        res = self.client.post(
            url,
            {
                "email": user.email,
                "otp": code,
                "new_password": "PasswordOne123!",
                "new_password_confirm": "PasswordTwo123!",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", str(res.data))

    # 38. Password reset confirm short password fails
    def test_38_password_reset_confirm_short_password_fails(self):
        user = User.objects.create_user(
            email="shortpw@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345697",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        url = reverse("password-reset-confirm")
        res = self.client.post(
            url,
            {
                "email": user.email,
                "otp": code,
                "new_password": "short",
                "new_password_confirm": "short",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("at least 8 characters", str(res.data).lower())

    # 39. Registration and password reset OTP purpose isolation
    def test_39_registration_and_password_reset_otp_purpose_isolation(self):
        user = User.objects.create_user(
            email="crossflow@example.com",
            password="OldPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345698",
            is_verified=False,
        )
        # Create a registration OTP
        reg_otp, reg_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.REGISTRATION)
        # Create a password reset OTP
        reset_otp, reset_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        # 1. Both OTPs are active and separate
        reg_otp.refresh_from_db()
        reset_otp.refresh_from_db()
        self.assertFalse(reg_otp.is_used)
        self.assertFalse(reset_otp.is_used)

        # 2. Registration OTP cannot be used to confirm password reset
        confirm_url = reverse("password-reset-confirm")
        res_reset_with_reg = self.client.post(
            confirm_url,
            {
                "email": user.email,
                "otp": reg_code,
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
        )
        self.assertEqual(res_reset_with_reg.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Password reset OTP cannot be used to verify registration
        verify_url = reverse("user-verify-otp")
        res_verify_with_reset = self.client.post(
            verify_url,
            {"email": user.email, "otp": reset_code},
        )
        self.assertEqual(res_verify_with_reset.status_code, status.HTTP_400_BAD_REQUEST)

        # User is still unverified and password unchanged
        user.refresh_from_db()
        self.assertFalse(user.is_verified)
        self.assertTrue(user.check_password("OldPassword123!"))

    # 40. Login OTP Step 1 dispatches login OTP and returns no JWT tokens
    def test_40_login_otp_step1_dispatches_otp_and_no_jwt(self):
        user = User.objects.create_user(
            email="step1test@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345701",
            is_verified=True,
        )
        url = reverse("token-obtain-pair")
        res = self.client.post(url, {"email": user.email, "password": "SecurePassword123!"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get("login_otp_required"))
        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)

        # Verify DB object exists with LOGIN purpose
        otp_record = EmailOTP.objects.filter(
            user=user,
            purpose=EmailOTP.OTPPurpose.LOGIN,
            is_used=False,
        ).first()
        self.assertIsNotNone(otp_record)
        self.assertFalse(otp_record.is_expired())

    # 41. Login OTP Step 2 valid code issues access and refresh JWT tokens
    def test_41_login_otp_step2_valid_code_issues_jwt_and_user_profile(self):
        user = User.objects.create_user(
            email="step2test@example.com",
            password="SecurePassword123!",
            first_name="Step2",
            last_name="Tester",
            role=UserRole.DONOR,
            phone_number="9812345702",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        verify_url = reverse("user-login-otp-verify")
        res = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("tokens", res.data)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["email"], user.email)

    # 42. Login OTP wrong code fails and decrements attempts
    def test_42_login_otp_wrong_code_fails_and_decrements_attempts(self):
        user = User.objects.create_user(
            email="wrongloginotp@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345703",
            is_verified=True,
        )
        otp_obj, _ = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        verify_url = reverse("user-login-otp-verify")
        res = self.client.post(verify_url, {"email": user.email, "otp": "000000"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("4 attempts remaining", str(res.data))
        otp_obj.refresh_from_db()
        self.assertEqual(otp_obj.attempts, 1)

    # 43. Login OTP lockout after 5 failed attempts
    def test_43_login_otp_lockout_after_5_failed_attempts(self):
        user = User.objects.create_user(
            email="loginlockout@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345704",
            is_verified=True,
        )
        otp_obj, valid_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        verify_url = reverse("user-login-otp-verify")
        last_fail_res = None
        for _ in range(5):
            last_fail_res = self.client.post(verify_url, {"email": user.email, "otp": "999999"})
            self.assertEqual(last_fail_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 5th attempt returns Maximum verification attempts exceeded
        self.assertIsNotNone(last_fail_res)
        self.assertIn("exceeded", str(last_fail_res.data).lower())

        # 6th attempt with valid code is rejected because OTP is locked (is_used=True)
        res_valid = self.client.post(verify_url, {"email": user.email, "otp": valid_code})
        self.assertEqual(res_valid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            "exceeded" in str(res_valid.data).lower() or "no active" in str(res_valid.data).lower()
        )

    # 44. Login OTP expired code rejected
    def test_44_login_otp_expired_code_rejected(self):
        user = User.objects.create_user(
            email="loginexpired@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345705",
            is_verified=True,
        )
        otp_obj, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        # Fast-forward expiry into past
        otp_obj.expires_at = timezone.now() - timedelta(minutes=1)
        otp_obj.save(update_fields=["expires_at"])

        verify_url = reverse("user-login-otp-verify")
        res = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(res.data).lower())

    # 45. Login OTP single-use: reused code fails
    def test_45_login_otp_single_use_reused_code_fails(self):
        user = User.objects.create_user(
            email="loginreused@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345706",
            is_verified=True,
        )
        _, code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        verify_url = reverse("user-login-otp-verify")

        # First use succeeds
        res1 = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Second use fails
        res2 = self.client.post(verify_url, {"email": user.email, "otp": code})
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    # 46. Login OTP resend invalidates previous login OTP
    def test_46_login_otp_resend_invalidates_previous_otp(self):
        user = User.objects.create_user(
            email="loginresend@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345707",
            is_verified=True,
        )
        old_otp, old_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)
        resend_url = reverse("user-login-otp-resend")
        res = self.client.post(resend_url, {"email": user.email})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Old OTP is now invalidated
        old_otp.refresh_from_db()
        self.assertTrue(old_otp.is_used)

        # Old code cannot be verified
        verify_url = reverse("user-login-otp-verify")
        res_old = self.client.post(verify_url, {"email": user.email, "otp": old_code})
        self.assertEqual(res_old.status_code, status.HTTP_400_BAD_REQUEST)

    # 47. Registration OTP cannot authenticate login
    def test_47_login_otp_registration_otp_cannot_be_used_for_login(self):
        user = User.objects.create_user(
            email="regisolation@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345708",
            is_verified=True,
        )
        _, reg_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.REGISTRATION)

        verify_login_url = reverse("user-login-otp-verify")
        res = self.client.post(verify_login_url, {"email": user.email, "otp": reg_code})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 48. Password reset OTP cannot authenticate login
    def test_48_login_otp_password_reset_otp_cannot_be_used_for_login(self):
        user = User.objects.create_user(
            email="resetisolation@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345709",
            is_verified=True,
        )
        _, reset_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.PASSWORD_RESET)

        verify_login_url = reverse("user-login-otp-verify")
        res = self.client.post(verify_login_url, {"email": user.email, "otp": reset_code})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 49. Login OTP cannot be used for registration verification or password reset
    def test_49_login_otp_cannot_be_used_for_registration_or_password_reset(self):
        user = User.objects.create_user(
            email="logintoother@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone_number="9812345710",
            is_verified=False,
        )
        _, login_code = EmailOTP.create_otp(user, purpose=EmailOTP.OTPPurpose.LOGIN)

        # Cannot verify registration
        verify_reg_url = reverse("user-verify-otp")
        res_reg = self.client.post(verify_reg_url, {"email": user.email, "otp": login_code})
        self.assertEqual(res_reg.status_code, status.HTTP_400_BAD_REQUEST)

        # Cannot confirm password reset
        confirm_reset_url = reverse("password-reset-confirm")
        res_reset = self.client.post(
            confirm_reset_url,
            {
                "email": user.email,
                "otp": login_code,
                "new_password": "NewDifferentPassword123!",
                "new_password_confirm": "NewDifferentPassword123!",
            },
        )
        self.assertEqual(res_reset.status_code, status.HTTP_400_BAD_REQUEST)

    # 50. Wrong password generates NO login OTP
    def test_50_wrong_password_does_not_generate_login_otp(self):
        user = User.objects.create_user(
            email="wrongpwotp@example.com",
            password="CorrectPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345711",
            is_verified=True,
        )
        url = reverse("token-obtain-pair")
        res = self.client.post(url, {"email": user.email, "password": "WrongPassword999!"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(EmailOTP.objects.filter(user=user, purpose=EmailOTP.OTPPurpose.LOGIN).exists())

    # 51. Unverified account generates NO login OTP and cannot verify login
    def test_51_unverified_account_does_not_generate_login_otp(self):
        user = User.objects.create_user(
            email="unverifiedlogin@example.com",
            password="CorrectPassword123!",
            role=UserRole.DONOR,
            phone_number="9812345712",
            is_verified=False,
        )
        url = reverse("token-obtain-pair")
        res = self.client.post(url, {"email": user.email, "password": "CorrectPassword123!"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(EmailOTP.objects.filter(user=user, purpose=EmailOTP.OTPPurpose.LOGIN).exists())

        # Direct verify call on unverified account also rejected
        verify_url = reverse("user-login-otp-verify")
        res_direct = self.client.post(verify_url, {"email": user.email, "otp": "123456"})
        self.assertEqual(res_direct.status_code, status.HTTP_401_UNAUTHORIZED)

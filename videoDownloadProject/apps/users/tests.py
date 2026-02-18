from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.users.models import SubscriptionEvent, UserProfile


class UsersHtmxFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="old-pass-123",
        )

    def test_create_account_success_toast_requires_htmx(self):
        response = self.client.get(reverse("apps.users:create_account_success_toast"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")

    def test_create_account_success_toast_htmx_renders_partial(self):
        response = self.client.get(
            reverse("apps.users:create_account_success_toast"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account Created")

    def test_change_password_htmx_get_renders_panel(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("apps.users:change_password"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Change password")

    def test_change_password_htmx_post_updates_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("apps.users:change_password"),
            data={
                "old_password": "old-pass-123",
                "new_password1": "new-pass-123-OK",
                "new_password2": "new-pass-123-OK",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password updated")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-pass-123-OK"))

    def test_close_change_password_panel_htmx_returns_empty(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("apps.users:change_password_close"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")

    def test_logout_htmx_redirects_to_index(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("apps.users:logout_user"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("apps.downloads:index"))


class SubscriptionFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="subscriber",
            email="subscriber@example.com",
            password="pass-12345",
        )

    def test_pricing_page_loads(self):
        response = self.client.get(reverse("pricing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Simple plans, clear limits")

    def test_start_checkout_requires_authentication(self):
        response = self.client.post(reverse("apps.users:start_pro_checkout"))
        self.assertEqual(response.status_code, 302)

    def test_start_checkout_redirects_to_payment_page(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("apps.users:start_pro_checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("apps.users:pro_checkout"))

    def test_checkout_page_requires_pending_session(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("apps.users:pro_checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pricing"))

    def test_activate_pro_requires_pending_checkout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("apps.users:activate_pro_subscription"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pricing"))

    def test_activate_pro_upgrades_profile_after_checkout(self):
        self.client.force_login(self.user)
        self.client.post(reverse("apps.users:start_pro_checkout"))
        response = self.client.post(reverse("apps.users:activate_pro_subscription"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('pricing')}?subscription=pro_activated")

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.plan_tier, UserProfile.PLAN_PRO)
        self.assertEqual(profile.max_resolution, 2160)
        self.assertTrue(profile.is_unlimited)

    def test_cancel_pro_requires_authentication(self):
        response = self.client.post(reverse("apps.users:cancel_pro_subscription"))
        self.assertEqual(response.status_code, 302)

    def test_cancel_pro_downgrades_to_free(self):
        self.client.force_login(self.user)
        profile = UserProfile.objects.get(user=self.user)
        profile.apply_plan(UserProfile.PLAN_PRO)
        profile.save(update_fields=["plan_tier", "daily_limit", "max_resolution", "is_unlimited"])

        response = self.client.post(reverse("apps.users:cancel_pro_subscription"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('pricing')}?subscription=pro_canceled")

        profile.refresh_from_db()
        self.assertEqual(profile.plan_tier, UserProfile.PLAN_FREE)
        self.assertEqual(profile.max_resolution, 720)
        self.assertFalse(profile.is_unlimited)


class ProviderSubscriptionEventTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="billing-user",
            email="billing@example.com",
            password="pass-12345",
        )
        self.profile = self.user.profile
        self.url = reverse("apps.users:provider_subscription_event")
        self.secret = "test-webhook-secret"

    def test_provider_event_rejects_invalid_secret(self):
        response = self.client.post(
            self.url,
            data={"id": "evt_1", "type": "subscription.activated", "data": {"user_id": self.user.id}},
            content_type="application/json",
            HTTP_X_SUBSCRIPTION_WEBHOOK_SECRET="bad-secret",
        )
        self.assertEqual(response.status_code, 403)

    def test_provider_event_activates_pro_and_is_idempotent(self):
        payload = {
            "id": "evt_activated_1",
            "type": "subscription.activated",
            "data": {
                "user_id": self.user.id,
                "provider_customer_id": "cus_123",
                "provider_subscription_id": "sub_123",
                "status": "active",
            },
        }
        with self.settings(SUBSCRIPTION_WEBHOOK_SECRET=self.secret):
            first = self.client.post(
                self.url,
                data=payload,
                content_type="application/json",
                HTTP_X_SUBSCRIPTION_WEBHOOK_SECRET=self.secret,
            )
            second = self.client.post(
                self.url,
                data=payload,
                content_type="application/json",
                HTTP_X_SUBSCRIPTION_WEBHOOK_SECRET=self.secret,
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertJSONEqual(second.content, {"ok": True, "status": "duplicate"})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.plan_tier, UserProfile.PLAN_PRO)
        self.assertEqual(self.profile.subscription_state, UserProfile.SUBSCRIPTION_ACTIVE)
        self.assertEqual(self.profile.provider_customer_id, "cus_123")
        self.assertEqual(self.profile.provider_subscription_id, "sub_123")
        self.assertEqual(SubscriptionEvent.objects.filter(event_id="evt_activated_1").count(), 1)

    def test_provider_event_cancels_subscription(self):
        self.profile.apply_plan(UserProfile.PLAN_PRO)
        self.profile.save()
        payload = {
            "id": "evt_cancel_1",
            "type": "customer.subscription.deleted",
            "data": {"user_id": self.user.id},
        }
        with self.settings(SUBSCRIPTION_WEBHOOK_SECRET=self.secret):
            response = self.client.post(
                self.url,
                data=payload,
                content_type="application/json",
                HTTP_X_SUBSCRIPTION_WEBHOOK_SECRET=self.secret,
            )

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.plan_tier, UserProfile.PLAN_FREE)
        self.assertEqual(self.profile.subscription_state, UserProfile.SUBSCRIPTION_CANCELED)

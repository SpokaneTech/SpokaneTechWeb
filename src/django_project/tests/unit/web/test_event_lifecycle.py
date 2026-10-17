"""Reconciliation, cancellation, conservative merges, and change announcements."""

import json
import os
from datetime import timedelta
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from web.event_ingestion import save_source_event
from web.models import Event
from web.tasks import (
    ingest_future_eventbrite_events,
    ingest_future_meetup_events,
    launch_reminders_for_tomorrows_events,
    post_event_to_discord,
    post_event_to_linkedin,
    post_weekly_event_summary_to_discord,
)
from web.utilities.scrapers.eventbrite import get_events_for_organization
from web.utilities.scrapers.meetup import get_event_information


class EventReconciliationTests(TestCase):
    def setUp(self):
        self.platform = baker.make("web.SocialPlatform", name="Meetup")
        self.group = baker.make("web.TechGroup", name="Builders", platform=self.platform)
        self.group.links.add(baker.make("web.Link", name="Builders Meetup page", url="https://www.meetup.com/builders"))
        self.event = baker.make(
            Event,
            group=self.group,
            name="Original event",
            social_platform_id="12345",
            start_datetime=timezone.now() + timedelta(days=3),
            url="https://www.meetup.com/builders/events/12345/",
            location_name="Original venue",
            location_address="123 Main Street",
            map_link="https://example.com/original-map",
        )

    def test_missing_meetup_listing_is_rechecked_and_can_cancel(self):
        with (
            patch("web.tasks.get_event_links", return_value=[]),
            patch("web.tasks.get_event_information", return_value={"status": "cancelled"}) as fetch,
        ):
            ingest_future_meetup_events(self.group.pk)
        fetch.assert_called_once_with(self.event.url)
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_cancelled)
        self.assertEqual(self.event.name, "Original event")
        self.assertIsNotNone(self.event.source_last_checked_at)
        self.assertEqual(Event.objects.count(), 1)

    def test_listing_failure_still_rechecks_known_events(self):
        with (
            patch("web.tasks.get_event_links", side_effect=RuntimeError("unavailable")),
            patch("web.tasks.get_event_information", return_value={"status": "cancelled"}),
        ):
            ingest_future_meetup_events(self.group.pk)
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_cancelled)

    def test_empty_or_failed_recheck_does_not_cancel_or_erase_location(self):
        for result in ({}, RuntimeError("temporary failure")):
            with (
                self.subTest(result=result),
                patch("web.tasks.get_event_links", return_value=[]),
                patch(
                    "web.tasks.get_event_information",
                    **({"side_effect": result} if isinstance(result, Exception) else {"return_value": result}),
                ),
            ):
                ingest_future_meetup_events(self.group.pk)
                self.event.refresh_from_db()
                self.assertFalse(self.event.is_cancelled)
                self.assertIsNone(self.event.source_last_checked_at)
                self.assertEqual(self.event.location_name, "Original venue")

    def test_location_change_then_partial_scrape_preserves_confirmed_fields(self):
        data = {
            "name": self.event.name,
            "social_platform_id": "12345",
            "location_name": "New venue",
            "location_address": "456 New Street",
            "map_link": "https://example.com/new-map",
        }
        save_source_event(self.group, data, location_complete=True)
        save_source_event(
            self.group,
            {
                "social_platform_id": "12345",
                "name": self.event.name,
                "location_name": "",
                "location_address": "",
                "map_link": "",
            },
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.location_name, "New venue")
        self.assertEqual(self.event.location_address, "456 New Street")
        self.assertEqual(self.event.map_link, "https://example.com/new-map")

    def test_confirmed_online_change_clears_physical_location(self):
        save_source_event(
            self.group,
            {
                "social_platform_id": "12345",
                "name": self.event.name,
                "location_name": "Online event",
                "location_address": "",
                "map_link": "",
            },
            location_complete=True,
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.location_name, "Online event")
        self.assertEqual(self.event.location_address, "")
        self.assertEqual(self.event.map_link, "")

    def test_cancelled_event_stays_cancelled_without_explicit_reinstatement(self):
        save_source_event(self.group, {"status": "cancelled"}, existing_pk=self.event.pk)
        save_source_event(self.group, {"name": self.event.name}, existing_pk=self.event.pk)
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_cancelled)
        save_source_event(self.group, {"status": "active"}, existing_pk=self.event.pk)
        self.event.refresh_from_db()
        self.assertFalse(self.event.is_cancelled)

    def test_rescheduled_event_keeps_identity_and_invalid_dates_do_not_erase_it(self):
        new_start = self.event.start_datetime + timedelta(days=1)
        save_source_event(self.group, {"social_platform_id": "12345", "start_datetime": new_start.isoformat()})
        save_source_event(
            self.group, {"social_platform_id": "12345", "name": "Renamed", "start_datetime": "not-a-date"}
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.start_datetime, new_start)
        self.assertEqual(Event.objects.count(), 1)

    def test_identical_ids_from_different_groups_do_not_overwrite(self):
        other = baker.make("web.TechGroup", platform=self.platform)
        save_source_event(
            other, {"social_platform_id": "12345", "name": "Other event", "start_datetime": self.event.start_datetime}
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Original event")
        self.assertEqual(Event.objects.count(), 2)

    def test_imported_tags_removed_but_local_topics_preserved(self):
        local = baker.make("web.Tag", value="Local")
        self.event.tags.add(local)
        save_source_event(self.group, {"name": self.event.name}, existing_pk=self.event.pk, tags=["Python", "Django"])
        save_source_event(self.group, {"name": self.event.name}, existing_pk=self.event.pk, tags=["Python"])
        self.assertEqual(set(self.event.tags.values_list("value", flat=True)), {"Local", "Python"})
        save_source_event(self.group, {"name": self.event.name}, existing_pk=self.event.pk, tags=None)
        self.assertEqual(self.event.tags.count(), 2)

    def test_eventbrite_missing_listing_rechecks_id_outside_discovery_window(self):
        self.platform.name = "Eventbrite"
        self.platform.save()
        self.group.links.clear()
        self.group.links.add(
            baker.make("web.Link", name="Builders Eventbrite page", url="https://www.eventbrite.com/o/builders-123")
        )
        with (
            patch("web.tasks.get_events_for_organization", return_value=[]),
            patch("web.tasks.get_event_record", return_value={"id": "12345", "status": "canceled"}) as fetch,
        ):
            ingest_future_eventbrite_events(self.group.pk)
        fetch.assert_called_once_with("12345")
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_cancelled)

    def test_eventbrite_detail_failure_does_not_stop_other_events(self):
        self.platform.name = "Eventbrite"
        self.platform.save()
        self.group.links.clear()
        self.group.links.add(
            baker.make("web.Link", name="Builders Eventbrite page", url="https://www.eventbrite.com/o/builders-123")
        )
        entries = [
            {"id": str(i), "name": {"text": str(i)}, "start": {"utc": self.event.start_datetime.isoformat()}}
            for i in [1, 2]
        ]
        with (
            patch("web.tasks.get_events_for_organization", return_value=entries),
            patch("web.tasks.get_event_details", side_effect=[RuntimeError("failed"), {"status": "live"}]),
            patch("web.tasks.get_event_record", return_value={}),
        ):
            ingest_future_eventbrite_events(self.group.pk)
        self.assertTrue(Event.objects.filter(social_platform_id="2").exists())
        self.assertFalse(Event.objects.filter(social_platform_id="1").exists())


class ProviderLifecycleParsingTests(TestCase):
    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_only_requested_event_can_confirm_cancellation(self, fetch):
        requested = {"__typename": "Event", "id": "12345", "status": "PUBLISHED"}
        other = {"__typename": "Event", "id": "999", "status": "CANCELLED"}
        for state, expected in [(requested, "active"), ({**requested, "status": "CANCELLED"}, "cancelled")]:
            with self.subTest(expected=expected):
                fetch.return_value = f'<script type="application/json">{json.dumps([state, other])}</script>'
                result = get_event_information("https://www.meetup.com/builders/events/12345/")
                self.assertEqual(result["status"], expected)

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_json_ld_cancelled_event_and_unknown_status(self, fetch):
        url = "https://www.meetup.com/builders/events/12345/"
        fetch.return_value = f'<script type="application/ld+json">{json.dumps({"@type": "Event", "url": url, "eventStatus": "https://schema.org/EventCancelled"})}</script>'
        self.assertEqual(get_event_information(url)["status"], "cancelled")
        fetch.return_value = "<h1>Event not found</h1>"
        self.assertNotIn("status", get_event_information(url))

    @override_settings(EVENTBRITE_API_KEY="test-token")
    @patch("web.utilities.scrapers.eventbrite.requests.get")
    def test_eventbrite_pagination_fetches_later_pages(self, get):
        first = Mock()
        first.json.return_value = {"events": [{"id": "1"}], "pagination": {"has_more_items": True, "page_count": 2}}
        second = Mock()
        second.json.return_value = {"events": [{"id": "2"}], "pagination": {"has_more_items": False}}
        get.side_effect = [first, second]
        self.assertEqual([item["id"] for item in get_events_for_organization("123")], ["1", "2"])
        self.assertIn("page=2", get.call_args.args[0])


@override_settings(POST_TO_DISCORD=True, POST_TO_LINKEDIN=True, DISCORD_WEBHOOK_URL="https://example.com/webhook")
class EventChangeNotificationTests(TestCase):
    def setUp(self):
        self.group = baker.make("web.TechGroup", enabled=True)
        self.event = baker.make(
            Event, group=self.group, start_datetime=timezone.now() + timedelta(days=3), location_name="Old venue"
        )

    def test_changed_location_announced_once_after_commit_noop_not_announced(self):
        with (
            patch("web.signals.post_event_to_discord.s") as discord,
            patch("web.signals.post_event_to_linkedin.s") as linkedin,
        ):
            with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
                self.event.location_name = "New venue"
                self.event.save(update_fields=["location_name"])
                discord.assert_not_called()
            discord.assert_called_once()
            linkedin.assert_called_once()
            kwargs = discord.call_args.kwargs
            self.assertIn("Event updated", kwargs["change_message"])
            self.assertIn("New venue", kwargs["change_message"])
            self.assertIn("venue", kwargs["change_message"])
            self.event.refresh_from_db()
            self.assertEqual(kwargs["change_version"], self.event.change_version)
            discord.reset_mock()
            linkedin.reset_mock()
            with self.captureOnCommitCallbacks(execute=True):
                self.event.save()
            discord.assert_not_called()
            linkedin.assert_not_called()

    def test_cancel_and_reinstate_have_explicit_labels(self):
        for status, label in [(Event.Status.CANCELLED, "Event cancelled"), (Event.Status.ACTIVE, "Event reinstated")]:
            with (
                patch("web.signals.post_event_to_discord.s") as discord,
                patch("web.signals.post_event_to_linkedin.s"),
                self.captureOnCommitCallbacks(execute=True),
            ):
                self.event.status = status
                self.event.save(update_fields=["status"])
            self.assertIn(label, discord.call_args.kwargs["change_message"])

    @override_settings(POST_TO_DISCORD=False, POST_TO_LINKEDIN=False)
    def test_disabled_notifications_and_rollback_do_not_publish(self):
        with (
            patch("web.signals.post_event_to_discord.s") as discord,
            patch("web.signals.post_event_to_linkedin.s") as linkedin,
            self.captureOnCommitCallbacks(execute=True),
        ):
            self.event.location_name = "Changed"
            self.event.save()
        discord.assert_not_called()
        linkedin.assert_not_called()
        with (
            override_settings(POST_TO_DISCORD=True),
            patch("web.signals.post_event_to_discord.s") as discord,
            self.captureOnCommitCallbacks(execute=True),
        ):
            try:
                with transaction.atomic():
                    self.event.status = Event.Status.CANCELLED
                    self.event.save()
                    raise ValueError("rollback")
            except ValueError:
                pass
        discord.assert_not_called()

    @patch("web.tasks.DiscordNotifier")
    def test_cancelled_and_stale_jobs_cannot_send_creation_or_reminder(self, notifier):
        self.event.status = Event.Status.CANCELLED
        self.event.save()
        self.assertIn("cancelled", post_event_to_discord(self.event.pk, is_new=True))
        self.assertIn("cancelled", post_event_to_discord(self.event.pk, is_new=False))
        self.assertIn("obsolete", post_event_to_discord(self.event.pk, change_message="old", change_version=0))
        notifier.assert_not_called()
        self.assertIn(
            "successfully",
            post_event_to_discord(
                self.event.pk, change_message="Event cancelled", change_version=self.event.change_version
            ),
        )
        notifier.return_value.send_message.assert_called_once()
        payload = notifier.return_value.send_message.call_args.args[0]
        self.assertEqual(payload["allowed_mentions"], {"parse": []})

    @override_settings(LINKEDIN_ACCESS_TOKEN="test", LINKEDIN_ORGANIZATION_URN="urn:li:organization:123")
    @patch("web.tasks.LinkedInOrganizationClient")
    def test_linkedin_cancelled_reminder_skipped_and_change_has_no_ai_prompt(self, client):
        self.event.status = Event.Status.CANCELLED
        self.event.save()
        self.assertIn("cancelled", post_event_to_linkedin(self.event.pk, is_new=False))
        client.assert_not_called()
        post_event_to_linkedin(
            self.event.pk, is_new=False, change_message="Event cancelled", change_version=self.event.change_version
        )
        client.return_value.post_organization_post.assert_called_once_with(commentary="Event cancelled")
        client.return_value.post_event.assert_not_called()


class CancelledEventVisibilityTests(TestCase):
    def setUp(self):
        self.group = baker.make("web.TechGroup", enabled=True)
        self.when = (timezone.localtime(timezone.now(), ZoneInfo("America/Los_Angeles")) + timedelta(days=1)).replace(
            hour=18, minute=0
        )
        self.cancelled = baker.make(
            Event,
            group=self.group,
            name="Cancelled meetup",
            status=Event.Status.CANCELLED,
            start_datetime=self.when,
            url="https://example.com/cancelled",
        )
        self.active = baker.make(
            Event, group=self.group, name="Active meetup", status=Event.Status.ACTIVE, start_datetime=self.when
        )

    def test_upcoming_surfaces_counts_and_calendar_exclude_cancelled(self):
        urls = [
            reverse("web:get_events", kwargs={"display": "list"}),
            reverse("web:index"),
            self.group.get_absolute_url(),
            reverse("web:event_calendar", kwargs={"year": self.when.year, "month": self.when.month}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_HX_REQUEST="true")
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, self.cancelled.name)
                self.assertContains(response, self.active.name)
        self.assertEqual(list(self.group.get_upcoming_events()), [self.active])
        response = self.client.get(reverse("web:get_techgroups", kwargs={"display": "list"}), HTTP_HX_REQUEST="true")
        self.assertContains(response, "1 upcoming event")
        self.assertNotContains(response, "2 upcoming events")

    def test_cancelled_detail_and_modal_still_exist_with_notice_and_no_rsvp(self):
        for url in [
            self.cancelled.get_absolute_url(),
            reverse("web:techevent_modal", kwargs={"pk": self.cancelled.pk}),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_HX_REQUEST="true")
                self.assertContains(response, "Event cancelled")
                self.assertContains(response, self.cancelled.name)
                self.assertNotContains(response, ">RSVP")

    @override_settings(POST_TO_DISCORD=True, DISCORD_WEBHOOK_URL="https://example.com/webhook")
    def test_reminders_and_weekly_summary_exclude_cancelled(self):
        with (
            patch("web.tasks.post_event_to_discord.s") as discord,
            patch("web.tasks.post_event_to_linkedin.s"),
            patch("web.tasks.DiscordNotifier") as notifier,
        ):
            launch_reminders_for_tomorrows_events()
            self.assertEqual([call.args[0] for call in discord.call_args_list], [self.active.pk])
            # Put both events inside the current week's interval even on Sunday.
            Event.objects.filter(pk__in=[self.active.pk, self.cancelled.pk]).update(start_datetime=timezone.now())
            with patch("web.tasks.timezone.now", return_value=timezone.now().replace(hour=0, minute=0, second=0)):
                post_weekly_event_summary_to_discord()
            notifier.return_value.post_weekly_summary.assert_called_once()
            records = notifier.return_value.post_weekly_summary.call_args.kwargs["event_list"]
            self.assertEqual(list(records.values_list("pk", flat=True)), [self.active.pk])

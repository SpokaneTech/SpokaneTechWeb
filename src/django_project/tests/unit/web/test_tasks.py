import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import django
from django.test import TestCase, override_settings

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

django.setup()
from model_bakery import baker
from web.models import Event, Tag
from web.signals import event_post_to_linkedin_signal
from web.tasks import (
    ingest_future_eventbrite_events,
    ingest_future_meetup_events,
    launch_reminders_for_tomorrows_events,
    post_event_to_discord,
    post_event_to_linkedin,
    post_weekly_event_summary_to_discord,
)
from web.utilities.scrapers.meetup import get_event_information


class TestIngestFutureEventbriteEvents(TestCase):
    def setUp(self):
        self.platform = baker.make("web.SocialPlatform", name="Eventbrite")
        self.group = baker.make("web.TechGroup", name="Test Eventbrite Group", platform=self.platform)
        self.link = baker.make(
            "web.Link",
            name=f"{self.group.name} {self.group.platform.name} page",
            url="https://www.eventbrite.com/o/test-eventbrite-group-12345",
        )
        self.group.links.add(self.link)

    @patch("web.tasks.get_events_for_organization")
    def test_returns_clear_result_when_platform_link_is_missing(self, mock_get_events_for_organization):
        self.group.links.remove(self.link)

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"no Eventbrite links found for {self.group.name}")
        mock_get_events_for_organization.assert_not_called()

    @patch("web.tasks.get_events_for_organization")
    def test_reads_organizer_id_from_numeric_only_eventbrite_url(self, mock_get_events_for_organization):
        self.link.url = "https://www.eventbrite.com/o/26948291755"
        self.link.save()
        mock_get_events_for_organization.return_value = []

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"added 0 new events for {self.group.name}")
        mock_get_events_for_organization.assert_called_once_with("26948291755")

    @patch("web.tasks.get_events_for_organization")
    def test_rejects_non_eventbrite_urls(self, mock_get_events_for_organization):
        self.link.url = "https://example.com/o/spokane-angel-alliance-26948291755"
        self.link.save()

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"invalid Eventbrite organization URL for {self.group.name}")
        mock_get_events_for_organization.assert_not_called()

    @patch("web.tasks.get_events_for_organization")
    def test_rejects_non_organization_eventbrite_urls(self, mock_get_events_for_organization):
        self.link.url = "https://www.eventbrite.com/e/spokane-angel-alliance-26948291755"
        self.link.save()

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"invalid Eventbrite organization URL for {self.group.name}")
        mock_get_events_for_organization.assert_not_called()

    @patch("web.tasks.get_event_details")
    @patch("web.tasks.get_events_for_organization")
    def test_ingests_event_without_primary_venue(self, mock_get_events_for_organization, mock_get_event_details):
        mock_get_events_for_organization.return_value = [
            {
                "id": "evt_123",
                "name": {"text": "Venue-less Event"},
                "description": {"text": "Online only."},
                "url": "https://example.com/events/evt_123",
                "start": {"utc": "2026-07-10T18:00:00Z"},
                "end": {"utc": "2026-07-10T19:00:00Z"},
            }
        ]
        mock_get_event_details.return_value = {"tags": [{"display_name": "Python"}]}

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"added 1 new events for {self.group.name}")
        event = Event.objects.get(social_platform_id="evt_123")
        self.assertEqual(event.location_name, "")
        self.assertEqual(event.location_address, "")
        self.assertEqual(event.map_link, "")
        self.assertEqual(list(event.tags.values_list("value", flat=True)), ["Python"])

    @patch("web.tasks.get_event_details")
    @patch("web.tasks.get_events_for_organization")
    def test_ingests_event_with_null_primary_venue_address(
        self, mock_get_events_for_organization, mock_get_event_details
    ):
        mock_get_events_for_organization.return_value = [
            {
                "id": "evt_456",
                "name": {"text": "Null Address Event"},
                "description": {"text": "Venue present, address missing."},
                "url": "https://example.com/events/evt_456",
                "start": {"utc": "2026-07-11T18:00:00Z"},
                "end": {"utc": "2026-07-11T19:00:00Z"},
            }
        ]
        mock_get_event_details.return_value = {
            "primary_venue": {"name": "Online", "address": None},
            "tags": [],
        }

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"added 1 new events for {self.group.name}")
        event = Event.objects.get(social_platform_id="evt_456")
        self.assertEqual(event.location_name, "Online")
        self.assertEqual(event.location_address, "")
        self.assertEqual(event.map_link, "")

    @patch("web.tasks.get_event_details")
    @patch("web.tasks.get_events_for_organization")
    def test_truncates_eventbrite_fields_to_model_limits(
        self, mock_get_events_for_organization, mock_get_event_details
    ):
        long_location_name = "LaunchPad INW Eventbrite Venue Name That Is Much Longer Than Sixty Four Characters"
        long_location_address = (
            "123 Long Address Lane, Spokane, WA 99201, United States, Building 7, Floor 12, Suite 1200"
        )

        mock_get_events_for_organization.return_value = [
            {
                "id": "evt_789",
                "name": {"text": "A" * 300},
                "description": {"text": "Oversized venue metadata."},
                "url": "https://example.com/events/evt_789",
                "start": {"utc": "2026-09-16T18:00:00Z"},
                "end": {"utc": "2026-09-16T19:00:00Z"},
            }
        ]
        mock_get_event_details.return_value = {
            "primary_venue": {
                "name": long_location_name,
                "address": {"localized_address_display": long_location_address},
            },
            "tags": [],
        }

        result = ingest_future_eventbrite_events(self.group.pk)

        self.assertEqual(result, f"added 1 new events for {self.group.name}")
        event = Event.objects.get(social_platform_id="evt_789")
        self.assertEqual(event.name, "A" * 255)
        self.assertEqual(event.location_name, long_location_name[:64])
        self.assertEqual(event.location_address, long_location_address[:256])


class TestMeetupEventInformation(TestCase):
    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_reads_venue_when_meetup_json_field_order_changes(self, mock_fetch_content):
        mock_fetch_content.return_value = """
            <script type="application/json">
              {"event":{"venue":{"country":"us","city":"Spokane","__typename":"Venue",
              "name":"Startup Spokane","state":"WA","address":"25 W Main Ave","id":"123"}}}
            </script>
        """

        event = get_event_information("https://www.meetup.com/example/events/123456/")

        self.assertEqual(event["location_name"], "Startup Spokane")
        self.assertEqual(event["location_address"], "25 W Main Ave, Spokane, WA, US")

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_leaves_missing_or_tbd_venue_blank(self, mock_fetch_content):
        mock_fetch_content.return_value = """
            <script type="application/json">
              {"event":{"venue":{"__typename":"Venue","name":"TBD","address":"123 Main St",
              "city":"Spokane","state":"WA","country":"US"}}}
            </script>
        """

        event = get_event_information("https://www.meetup.com/example/events/123456/")

        self.assertEqual(event["location_name"], "")
        self.assertEqual(event["location_address"], "")

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_leaves_location_blank_when_venue_is_absent(self, mock_fetch_content):
        mock_fetch_content.return_value = '<script type="application/json">{"event":{}}</script>'

        event = get_event_information("https://www.meetup.com/example/events/123456/")

        self.assertEqual(event["location_name"], "")
        self.assertEqual(event["location_address"], "")

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_reads_event_topics_and_resolves_apollo_references(self, fetch):
        payload = {
            "props": {
                "pageProps": {
                    "event": {
                        "id": "123456",
                        "topics": {
                            "edges": [
                                {"node": {"name": " Python "}},
                                {"node": {"__ref": "Topic:2"}},
                                {"node": {"name": "python"}},
                                {"node": {"name": ""}},
                                {"node": {}},
                            ]
                        },
                        "group": {"topics": [{"name": "Group-only topic"}]},
                    },
                    "__APOLLO_STATE__": {
                        "Topic:2": {"__typename": "Topic", "name": "AI &amp; Data"},
                        "Event:999": {"__typename": "Event", "id": "999", "topics": [{"name": "Other event"}]},
                    },
                }
            }
        }
        fetch.return_value = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        result = get_event_information("https://www.meetup.com/example/events/123456/")
        self.assertEqual(result["tags"], ["Python", "AI & Data"])

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_reads_event_from_normalized_cache_and_ignores_group_topics(self, fetch):
        payload = {
            "__APOLLO_STATE__": {
                "Event:123456": {"__typename": "Event", "id": "123456", "topics": {"nodes": [{"__ref": "Topic:1"}]}},
                "Topic:1": {"name": "Web Development"},
                "Group:1": {"topics": [{"name": "Group-only topic"}]},
            }
        }
        fetch.return_value = f'<script type="application/json">{json.dumps(payload)}</script>'
        result = get_event_information("https://www.meetup.com/example/events/123456/")
        self.assertEqual(result["tags"], ["Web Development"])

    @patch("web.utilities.scrapers.meetup.fetch_content_with_playwright")
    def test_missing_or_empty_event_topics_do_not_use_group_topics(self, fetch):
        for topics in (None, {}, {"edges": []}):
            with self.subTest(topics=topics):
                payload = {"event": {"topics": topics, "group": {"topics": [{"name": "Python"}]}}}
                fetch.return_value = f"<script>not JSON</script><script>{json.dumps(payload)}</script>"
                result = get_event_information("https://www.meetup.com/example/events/123456/")
                self.assertEqual(result["tags"], [])


class TestIngestFutureMeetupEvents(TestCase):
    def setUp(self):
        self.platform = baker.make("web.SocialPlatform", name="Meetup")
        self.group = baker.make("web.TechGroup", name="Test Meetup Group", platform=self.platform)
        self.link = baker.make(
            "web.Link",
            name=f"{self.group.name} {self.group.platform.name} page",
            url="https://www.meetup.com/test-meetup-group",
        )
        self.group.links.add(self.link)

    @patch("web.tasks.get_event_information")
    @patch("web.tasks.get_event_links")
    def test_truncates_venue_fields_before_saving(self, mock_get_event_links, mock_get_event_information):
        mock_get_event_links.return_value = ["https://www.meetup.com/test-meetup-group/events/123456/"]
        mock_get_event_information.return_value = {
            "name": "Test event",
            "url": "https://www.meetup.com/test-meetup-group/events/123456/",
            "social_platform_id": "123456",
            "start_datetime": "2026-09-20T18:00:00Z",
            "location_name": "N" * 65,
            "location_address": "A" * 257,
        }

        ingest_future_meetup_events(self.group.pk)

        event = Event.objects.get(social_platform_id="123456")
        self.assertEqual(event.location_name, "N" * 64)
        self.assertEqual(event.location_address, "A" * 256)

    @patch("web.tasks.get_event_information")
    @patch("web.tasks.get_event_links")
    def test_ingests_and_backfills_tags_without_duplicate_events_or_tags(self, links, information):
        links.return_value = ["https://www.meetup.com/test-meetup-group/events/123456/"]
        existing = baker.make("web.Tag", value="Python")
        data = {"name": "Tagged event", "social_platform_id": "123456", "start_datetime": "2026-09-20T18:00:00Z"}
        information.side_effect = [dict(data), {**data, "tags": ["Python", " Django ", "Python", "", None]}]
        ingest_future_meetup_events(self.group.pk)
        event = Event.objects.get(social_platform_id="123456")
        local = baker.make("web.Tag", value="Local topic")
        event.tags.add(local)
        result = ingest_future_meetup_events(self.group.pk)
        self.assertIn("added 0 new events", result)
        self.assertEqual(Event.objects.filter(social_platform_id="123456").count(), 1)
        self.assertEqual(set(event.tags.values_list("value", flat=True)), {"Python", "Django", "Local topic"})
        self.assertTrue(event.tags.filter(pk=existing.pk).exists())
        self.assertEqual(Tag.objects.filter(value="Python").count(), 1)
        information.side_effect = None
        information.return_value = {**data, "tags": []}
        ingest_future_meetup_events(self.group.pk)
        self.assertEqual(set(event.tags.values_list("value", flat=True)), {"Local topic"})

    @patch("web.tasks.get_event_information")
    @patch("web.tasks.get_event_links")
    def test_tag_limit_and_name_date_fallback(self, links, information):
        links.return_value = ["https://www.meetup.com/test-meetup-group/events/123456/"]
        information.return_value = {
            "name": "Fallback tagged event",
            "start_datetime": "2026-09-20T18:00:00Z",
            "tags": ["A" * 80],
        }
        ingest_future_meetup_events(self.group.pk)
        event = Event.objects.get(name="Fallback tagged event")
        self.assertEqual(list(event.tags.values_list("value", flat=True)), ["A" * 64])

    @patch("web.tasks.get_event_information", return_value={})
    @patch("web.tasks.get_event_links")
    def test_empty_scrape_does_not_create_event_or_tags(self, links, information):
        links.return_value = ["https://www.meetup.com/test-meetup-group/events/123456/"]
        result = ingest_future_meetup_events(self.group.pk)
        self.assertIn("added 0 new events", result)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(Tag.objects.exists())


class TestPostEventToLinkedIn(TestCase):
    def test_skips_when_post_to_linkedin_setting_is_false(self):
        event = baker.make("web.Event")

        with (
            patch("web.tasks.settings.POST_TO_LINKEDIN", False),
            patch("web.tasks.LinkedInOrganizationClient") as mock_linkedin_client,
        ):
            result = post_event_to_linkedin(event.pk, is_new=True)

        self.assertEqual(result, f"POST_TO_LINKEDIN is False. Skipping LinkedIn post for event with pk {event.pk}.")
        mock_linkedin_client.assert_not_called()


@override_settings(DISCORD_WEBHOOK_URL="https://example.com/webhook")
class TestDiscordPostingSetting(TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 5, 18, tzinfo=timezone.utc)
        self.group = baker.make("web.TechGroup", name="Local builders", enabled=True)
        self.event = baker.make("web.Event", group=self.group, start_datetime=self.now + timedelta(days=1))

    @override_settings(POST_TO_DISCORD=False)
    @patch("web.tasks.DiscordNotifier")
    def test_disabled_tasks_skip_before_database_or_notifier_work(self, notifier):
        with self.assertNumQueries(0):
            result = post_event_to_discord(999999)
            summary = post_weekly_event_summary_to_discord()
        self.assertIn("POST_TO_DISCORD is False", result)
        self.assertIn("POST_TO_DISCORD is False", summary)
        notifier.assert_not_called()

    @override_settings(POST_TO_DISCORD=True)
    @patch("web.tasks.DiscordNotifier")
    def test_enabled_event_task_posts_new_events_and_reminders(self, notifier):
        for is_new in (True, False):
            with self.subTest(is_new=is_new):
                notifier.reset_mock()
                result = post_event_to_discord(self.event.pk, is_new=is_new)
                notifier.assert_called_once_with(webhook_url="https://example.com/webhook")
                notifier.return_value.post_event.assert_called_once_with(event=self.event, is_new=is_new)
                self.assertIn("posted to Discord successfully", result)

    @override_settings(POST_TO_DISCORD=True, DISCORD_WEBHOOK_URL=None)
    @patch("web.tasks.DiscordNotifier")
    def test_enabled_tasks_still_require_webhook(self, notifier):
        for result in (post_event_to_discord(self.event.pk), post_weekly_event_summary_to_discord()):
            self.assertIn("webhook URL not configured", result)
        notifier.assert_not_called()

    @override_settings(POST_TO_DISCORD=True)
    @patch("web.tasks.DiscordNotifier")
    def test_enabled_weekly_summary_posts_matching_events(self, notifier):
        with patch("web.tasks.timezone.now", return_value=self.now):
            result = post_weekly_event_summary_to_discord()
        notifier.assert_called_once_with(webhook_url="https://example.com/webhook")
        events = notifier.return_value.post_weekly_summary.call_args.kwargs["event_list"]
        self.assertEqual(list(events), [self.event])
        self.assertIn("posted to Discord successfully", result)

    def test_reminders_only_queue_discord_when_enabled(self):
        for enabled in (False, True):
            with (
                self.subTest(enabled=enabled),
                override_settings(POST_TO_DISCORD=enabled),
                patch("web.tasks.timezone.now", return_value=self.now),
                patch("web.tasks.post_event_to_discord.s") as discord,
                patch("web.tasks.post_event_to_linkedin.s") as linkedin,
            ):
                launch_reminders_for_tomorrows_events()
                if enabled:
                    discord.assert_called_once_with(self.event.pk, is_new=False)
                    discord.return_value.apply_async.assert_called_once()
                else:
                    discord.assert_not_called()
                linkedin.assert_called_once_with(self.event.pk, is_new=False)
                linkedin.return_value.apply_async.assert_called_once()

    def test_creation_signal_only_queues_discord_when_enabled(self):
        for enabled in (False, True):
            with (
                self.subTest(enabled=enabled),
                override_settings(POST_TO_DISCORD=enabled),
                patch("web.signals.post_event_to_discord.s") as discord,
                patch("web.signals.post_event_to_linkedin.s") as linkedin,
                self.captureOnCommitCallbacks(execute=True),
            ):
                event_post_to_linkedin_signal(Event, self.event, created=True)
            if enabled:
                discord.assert_called_once_with(self.event.pk, is_new=True)
                discord.return_value.apply_async.assert_called_once()
            else:
                discord.assert_not_called()
            linkedin.assert_called_once_with(self.event.pk, is_new=True)
            linkedin.return_value.apply_async.assert_called_once()

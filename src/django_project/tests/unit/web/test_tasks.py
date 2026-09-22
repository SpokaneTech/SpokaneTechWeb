import os
from pathlib import Path
from unittest.mock import patch

import django
from django.test import TestCase

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

django.setup()
from model_bakery import baker
from web.models import Event
from web.tasks import ingest_future_eventbrite_events, ingest_future_meetup_events, post_event_to_linkedin
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
    def test_ingests_event_with_null_primary_venue_address(self, mock_get_events_for_organization, mock_get_event_details):
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
    def test_truncates_eventbrite_fields_to_model_limits(self, mock_get_events_for_organization, mock_get_event_details):
        long_location_name = "LaunchPad INW Eventbrite Venue Name That Is Much Longer Than Sixty Four Characters"
        long_location_address = "123 Long Address Lane, Spokane, WA 99201, United States, Building 7, Floor 12, Suite 1200"

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

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
from web.tasks import ingest_future_eventbrite_events, post_event_to_linkedin


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

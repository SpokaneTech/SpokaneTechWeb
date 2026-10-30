"""Regression tests for safe, scoped Luma iCalendar ingestion."""

import os
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import django

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")
django.setup()

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from web.models import Event
from web.tasks import ingest_future_luma_events
from web.utilities.scrapers.luma import (
    is_coeur_dalene_location,
    normalize_event_url,
    parse_luma_calendar,
    validate_calendar_url,
)


def ics_event(uid="evt-approved@events.lu.ma", url="https://luma.com/build-3wx2", location=None, start=None):
    location = location or "Innovation Den, 418 E Lakeside Ave, Coeur d'Alene, ID 83814"
    start = start or (timezone.now() + timedelta(days=20))
    end = start + timedelta(minutes=75)
    return (
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        "SUMMARY:OpenClaw News\\, Tools\\, and Work Session\r\n"
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DESCRIPTION:Get details at: {url}\\nHosted by Nick Smoot\r\n"
        f"LOCATION:{location.replace(',', r'\,')}\r\n"
        "STATUS:TENTATIVE\r\n"
        "SEQUENCE:215499820\r\n"
        "END:VEVENT\r\n"
    )


def ics_feed(*events):
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Luma//build_cda//EN\r\n"
            + "".join(events) + "END:VCALENDAR\r\n").encode()


class LumaParserTests(TestCase):
    def test_parses_unescaped_location_and_factual_metadata_only(self):
        records = parse_luma_calendar(ics_feed(ics_event()))
        self.assertEqual(len(records), 1)
        event = records[0]
        self.assertEqual(event["social_platform_id"], "evt-approved@events.lu.ma")
        self.assertEqual(event["name"], "OpenClaw News, Tools, and Work Session")
        self.assertEqual(event["location_name"], "Innovation Den")
        self.assertEqual(event["url"], "https://luma.com/build-3wx2")
        self.assertTrue(event["location_complete"])
        self.assertTrue(timezone.is_aware(event["start_datetime"]))
        self.assertNotIn("Hosted by Nick Smoot", event["description"])

    def test_ignores_event_without_approved_domain_or_location(self):
        event = ics_event(url="https://example.com/event")
        self.assertEqual(parse_luma_calendar(ics_feed(event)), [])
        self.assertFalse(is_coeur_dalene_location("Online event"))
        self.assertFalse(is_coeur_dalene_location("418 E Lakeside Ave, Spokane, WA"))
        self.assertFalse(is_coeur_dalene_location("Coeur d'Alene, ID"))
        self.assertTrue(is_coeur_dalene_location("418 E Lakeside Ave, Coeur d'Alene, ID 83814"))

    def test_rejects_duplicate_uid(self):
        feed = ics_feed(ics_event(), ics_event())
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            parse_luma_calendar(feed)

    def test_normalizes_public_luma_hosts_and_rejects_invalid(self):
        self.assertEqual(normalize_event_url("https://lu.ma/build-3wx2"), "https://luma.com/build-3wx2")
        for url in ("http://luma.com/build-3wx2", "https://luma.com.evil.test/xxx",
                    "https://luma.com/event/evt-123", "https://luma.com/build-3wx2?private=1"):
            self.assertIsNone(normalize_event_url(url))

    def test_only_calendar_scoped_https_fetch_urls(self):
        validate_calendar_url("https://api.luma.com/ics/get?entity=calendar&id=cal-yFU7dz3kUHXxUDR")
        for url in ("https://example.com/ics/get?entity=calendar&id=cal-ok",
                    "http://api.luma.com/ics/get?entity=calendar&id=cal-ok",
                    "https://api.luma.com/ics/get?entity=user&id=cal-ok",
                    "https://api.luma.com/ics/get?entity=calendar&id=cal-ok&redirect=https://evil.test"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_calendar_url(url)


class LumaIngestionTests(TestCase):
    def setUp(self):
        platform = baker.make("web.SocialPlatform", name="Luma")
        self.group = baker.make("web.TechGroup", name="Idaho AI Agents", platform=platform)
        self.group.links.add(baker.make(
            "web.Link", name="Idaho AI Agents Luma feed",
            url="https://api.luma.com/ics/get?entity=calendar&id=cal-yFU7dz3kUHXxUDR",
        ))
        self.group.links.add(baker.make(
            "web.Link", name="Idaho AI Agents Luma approved event", url="https://luma.com/build-3wx2"
        ))

    def test_imports_only_approved_upcoming_coeur_dalene_events_idempotently(self):
        feed = ics_feed(
            ics_event(),
            ics_event(uid="evt-unrelated@events.lu.ma", url="https://luma.com/other-event"),
            ics_event(uid="evt-outside@events.lu.ma", url="https://luma.com/build-3wx2",
                      location="123 Main St, Spokane, WA 99201"),
        )
        with (patch("web.tasks.fetch_luma_calendar", return_value=feed) as fetch,
              patch("web.signals.post_event_to_linkedin.s") as linkedin,
              patch("web.signals.post_event_to_discord.s") as discord,
              self.captureOnCommitCallbacks(execute=True)):
            self.assertIn("added 1 new events", ingest_future_luma_events(self.group.pk))
            self.assertIn("added 0 new events", ingest_future_luma_events(self.group.pk))
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(Event.objects.filter(group=self.group).count(), 1)
        event = Event.objects.get(group=self.group)
        self.assertEqual(event.social_platform_id, "evt-approved@events.lu.ma")
        self.assertEqual(event.url, "https://luma.com/build-3wx2")
        self.assertEqual(event.location_name, "Innovation Den")
        self.assertFalse(event.description.startswith("Get details at:"))
        self.assertFalse(event.image_source_url)
        linkedin.assert_not_called()
        discord.assert_not_called()

    def test_rescheduled_event_keeps_source_identity(self):
        first = ics_feed(ics_event())
        second = ics_feed(ics_event(start=timezone.now() + timedelta(days=30)))
        with patch("web.tasks.fetch_luma_calendar", side_effect=[first, second]):
            ingest_future_luma_events(self.group.pk)
            original = Event.objects.get(group=self.group)
            ingest_future_luma_events(self.group.pk)
            updated = Event.objects.get(group=self.group)
        self.assertEqual(original.pk, updated.pk)
        self.assertNotEqual(original.start_datetime, updated.start_datetime)

    def test_missing_feed_event_does_not_cancel_or_delete_existing(self):
        with patch("web.tasks.fetch_luma_calendar", side_effect=[ics_feed(ics_event()), ics_feed()]):
            ingest_future_luma_events(self.group.pk)
            ingest_future_luma_events(self.group.pk)
        event = Event.objects.get(group=self.group)
        self.assertEqual(event.status, Event.Status.ACTIVE)

    def test_no_allowlist_causes_no_fetch(self):
        self.group.links.filter(name="Idaho AI Agents Luma approved event").delete()
        with patch("web.tasks.fetch_luma_calendar") as fetch:
            self.assertIn("no approved Luma event", ingest_future_luma_events(self.group.pk))
        fetch.assert_not_called()

    def test_unavailable_feed_does_not_change_records(self):
        existing = baker.make(
            Event, group=self.group, social_platform_id="evt-approved@events.lu.ma",
            name="Existing", start_datetime=timezone.now() + timedelta(days=5)
        )
        with patch("web.tasks.fetch_luma_calendar", side_effect=RuntimeError("provider down")):
            with self.assertRaises(RuntimeError):
                ingest_future_luma_events(self.group.pk)
        existing.refresh_from_db()
        self.assertEqual(existing.name, "Existing")
        self.assertEqual(Event.objects.filter(group=self.group).count(), 1)

    def test_fetch_rejects_ssrf_before_network_request(self):
        from web.utilities.scrapers.luma import fetch_luma_calendar
        with patch("web.utilities.scrapers.luma.requests.get") as get:
            with self.assertRaises(ValueError):
                fetch_luma_calendar("https://example.com/internal")
        get.assert_not_called()

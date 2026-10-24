"""Event tag hashtags across LinkedIn announcements, reminders and long posts."""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker
from web.models import Tag
from web.utilities.notifiers.linkedin import LinkedInOrganizationClient, add_event_hashtags, escape_linkedin_commentary


@override_settings(POST_TO_LINKEDIN=False, POST_TO_DISCORD=False, PROMOTE_SITE_LINKS=False)
class LinkedInEventHashtagTests(TestCase):
    def setUp(self):
        group = baker.make("web.TechGroup", enabled=True)
        self.event = baker.make(
            "web.Event",
            group=group,
            name="Community workshop",
            description="Learn together.",
            start_datetime=timezone.now() + timedelta(days=1),
            url="https://example.com/events/workshop",
        )
        self.client = LinkedInOrganizationClient("unused", "urn:li:organization:123")

    def test_tags_are_normalized_and_deduplicated_with_the_brand(self):
        for value in [
            "Python",
            "python",
            "Machine Learning",
            "Data-Science",
            "Café",
            "#spokanetech",
            "SpokaneTech",
            "!!!",
        ]:
            self.event.tags.add(baker.make(Tag, value=value))
        result = add_event_hashtags(self.event, "Join us.")
        hashtags = result.split("\n\n")[-1].split()
        self.assertEqual(set(hashtags), {"#spokanetech", "#Python", "#MachineLearning", "#DataScience", "#Café"})
        self.assertEqual(len(hashtags), 5)

    def test_untagged_events_still_include_spokanetech(self):
        self.assertEqual(add_event_hashtags(self.event, "Join us."), "Join us.\n\n#spokanetech")

    def test_escaped_budget_preserves_footer_and_hashtags(self):
        self.event.tags.add(baker.make(Tag, value="Python"))
        footer = "\n\nLocation: Library (South Hill)\nhttps://example.com/event"
        result = add_event_hashtags(self.event, "(SPUG) *project* " * 300, footer=footer)
        self.assertLessEqual(len(escape_linkedin_commentary(result)), 3000)
        self.assertTrue(result.endswith(footer + "\n\n#spokanetech #Python"))

    def test_footer_that_only_exceeds_limit_after_escaping_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "hashtags exceed"):
            add_event_hashtags(self.event, "Join us.", footer="(" * 1500)

    @patch("web.utilities.notifiers.linkedin.generate_post_content")
    def test_announcements_reminders_and_ai_fallbacks_include_hashtags(self, ai):
        self.event.tags.add(baker.make(Tag, value="Machine Learning"))
        for is_new in (True, False):
            for fallback in (False, True):
                with self.subTest(is_new=is_new, fallback=fallback):
                    ai.return_value = "Join the workshop."
                    ai.side_effect = ValueError("AI unavailable") if fallback else None
                    with patch.object(self.client, "post_organization_post") as post:
                        self.client.post_event(self.event, is_new=is_new)
                    commentary = post.call_args.args[0]
                    self.assertTrue(commentary.endswith("#spokanetech #MachineLearning"))
                    self.assertIn(self.event.url, commentary)
                    self.assertEqual(post.call_args.kwargs["article_url"], self.event.url)

    @patch("web.utilities.notifiers.linkedin.generate_post_content", return_value="A long announcement. " * 300)
    def test_truncation_preserves_event_links_details_and_all_hashtags(self, ai):
        self.event.start_datetime = datetime(2026, 10, 21, 0, 30, tzinfo=UTC)
        self.event.end_datetime = datetime(2026, 10, 21, 2, 30, tzinfo=UTC)
        self.event.tags.add(baker.make(Tag, value="Python"))
        for promote in (False, True):
            with self.subTest(promotion=promote), self.settings(PROMOTE_SITE_LINKS=promote):
                commentary = self.client.build_event_commentary(self.event)
                self.assertLessEqual(len(commentary), 3000)
                self.assertIn(self.event.url, commentary)
                self.assertIn("📅 Date:", commentary)
                self.assertIn("05:30 PM PDT – 07:30 PM PDT", commentary)
                self.assertTrue(commentary.endswith("#spokanetech #Python"))
                if promote:
                    self.assertIn("utm_source=linkedin", commentary)

    @patch("web.utilities.notifiers.linkedin.generate_post_content", return_value="Join us.")
    def test_scheduled_times_include_optional_end_date_and_pacific_offsets(self, ai):
        cases = [
            (
                datetime(2026, 10, 21, 0, 30, tzinfo=UTC),
                datetime(2026, 10, 21, 2, 30, tzinfo=UTC),
                "05:30 PM PDT – 07:30 PM PDT",
            ),
            (
                datetime(2026, 10, 21, 6, 30, tzinfo=UTC),
                datetime(2026, 10, 21, 8, 30, tzinfo=UTC),
                "11:30 PM PDT – 2026-10-21 01:30 AM PDT",
            ),
            (
                datetime(2026, 11, 1, 8, 30, tzinfo=UTC),
                datetime(2026, 11, 1, 9, 30, tzinfo=UTC),
                "01:30 AM PDT – 01:30 AM PST",
            ),
            (datetime(2026, 10, 21, 0, 30, tzinfo=UTC), None, "05:30 PM PDT"),
        ]
        for start, end, expected in cases:
            for is_new in (True, False):
                with self.subTest(start=start, end=end, is_new=is_new):
                    self.event.start_datetime = start
                    self.event.end_datetime = end
                    commentary = self.client.build_event_commentary(self.event, is_new=is_new)
                    time_line = next(line for line in commentary.splitlines() if line.startswith("⏰ Time:"))
                    self.assertEqual(time_line, f"⏰ Time: {expected}.")

    def test_excessive_tags_fail_explicitly_instead_of_silently_dropping_tags(self):
        tags = Tag.objects.bulk_create([Tag(value=f"Topic{index:02d}" + "a" * 57) for index in range(50)])
        self.event.tags.add(*tags)
        with self.assertRaisesRegex(ValueError, "hashtags exceed"):
            add_event_hashtags(self.event, "Join us.")

    @patch("web.utilities.notifiers.linkedin.generate_post_content", side_effect=requests.Timeout)
    def test_ai_network_failure_preserves_hashtags(self, ai):
        self.event.tags.add(baker.make(Tag, value="Python"))
        with self.assertLogs("web.utilities.notifiers.linkedin", level="WARNING") as logs:
            commentary = self.client.build_event_commentary(self.event)
        self.assertTrue(commentary.endswith("#spokanetech #Python"))
        self.assertIn(f"event {self.event.pk} (Timeout); using fallback text", logs.output[0])

    @override_settings(POST_TO_LINKEDIN=True, POST_TO_DISCORD=True)
    def test_ingestion_commits_tags_before_dispatching_both_announcements(self):
        from web.event_ingestion import save_source_event
        from web.models import Event

        observed = []

        def queued_commentary(pk, **kwargs):
            observed.append(add_event_hashtags(Event.objects.get(pk=pk), "Join us."))
            from unittest.mock import MagicMock
            return MagicMock()

        with (
            patch("web.event_ingestion.queue_event_image"),
            patch("web.signals.post_event_to_linkedin.s", side_effect=queued_commentary) as linkedin,
            patch("web.signals.post_event_to_discord.s") as discord,
            self.captureOnCommitCallbacks(execute=True),
        ):
            event, created = save_source_event(
                self.event.group,
                {"name": "New tagged event", "start_datetime": timezone.now() + timedelta(days=2)},
                tags=["Python", "Machine Learning"],
            )
            linkedin.assert_not_called()
            discord.assert_not_called()
        self.assertTrue(created)
        discord.assert_called_once_with(event.pk, is_new=True)
        linkedin.assert_called_once_with(event.pk, is_new=True)
        self.assertIn("#Python", observed[0])
        self.assertIn("#MachineLearning", observed[0])

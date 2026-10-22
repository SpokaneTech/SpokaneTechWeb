"""Discord announcements remain deliverable with oversized or unavailable AI output."""

import json
import os
from datetime import timedelta
from unittest.mock import patch

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker
from web.utilities.notifiers.discord import DiscordNotifier


@override_settings(POST_TO_DISCORD=False, POST_TO_LINKEDIN=False)
class DiscordPayloadTests(TestCase):
    def setUp(self):
        self.event = baker.make(
            "web.Event",
            group=baker.make("web.TechGroup", enabled=True),
            name="x" * 300,
            location_name="y" * 1100,
            start_datetime=timezone.now() + timedelta(days=1),
            url="https://example.com/event",
        )
        self.notifier = DiscordNotifier("https://example.com/webhook")

    @patch("web.utilities.notifiers.discord.generate_post_content", return_value="AI content " * 500)
    def test_generated_posts_respect_discord_limits_with_and_without_promotion(self, ai):
        for promote in (True, False):
            for is_new in (True, False):
                with self.subTest(promote=promote, is_new=is_new), self.settings(PROMOTE_SITE_LINKS=promote):
                    with patch("web.utilities.notifiers.discord.requests.post") as post:
                        self.notifier.post_event(self.event, is_new=is_new)
                    payload = json.loads(post.call_args.kwargs["data"])
                    self.assertLessEqual(len(payload["content"]), 2000)
                    embed = payload["embeds"][0]
                    self.assertLessEqual(len(embed["title"]), 256)
                    self.assertTrue(all(len(field["value"]) <= 1024 for field in embed["fields"]))

    @patch("web.utilities.notifiers.discord.generate_post_content", side_effect=requests.Timeout)
    def test_ai_network_failure_uses_fallback(self, ai):
        for builder in (self.notifier.build_event_created_message, self.notifier.build_event_reminder_message):
            self.assertIn(self.event.url, builder(self.event)["content"])

    @patch("web.utilities.notifiers.discord.requests.post")
    def test_send_disables_all_mentions_for_general_and_group_webhooks(self, post):
        content = "@everyone @here <@123> <@&456>"
        for url in (None, "https://example.com/group-webhook"):
            for mentions in (None, {"parse": ["everyone", "roles", "users"], "users": ["123"]}):
                with self.subTest(url=url, mentions=mentions):
                    payload = {"content": content}
                    if mentions is not None:
                        payload["allowed_mentions"] = mentions
                    self.notifier.send_message(payload, url=url)
                    sent = json.loads(post.call_args.kwargs["data"])
                    self.assertEqual(sent["allowed_mentions"], {"parse": []})
                    self.assertEqual(sent["content"], content)
                    self.assertEqual(post.call_args.args[0], url or self.notifier.webhook_url)
                    self.assertEqual(payload.get("allowed_mentions"), mentions)

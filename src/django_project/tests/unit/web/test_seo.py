"""Search publication, metadata, discovery, and provider-independent promotion."""

import json
import os
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from xml.etree import ElementTree

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from bs4 import BeautifulSoup
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from web.event_ingestion import save_source_event
from web.models import Event
from web.seo import campaign_url, public_origin
from web.utilities.notifiers.discord import DiscordNotifier
from web.utilities.notifiers.linkedin import LinkedInOrganizationClient


@override_settings(PUBLIC_SITE_URL="https://www.spokanetech.org", POST_TO_DISCORD=False, POST_TO_LINKEDIN=False)
class SEOTests(TestCase):
    def setUp(self):
        self.group = baker.make("web.TechGroup", name="Actual local builders", enabled=True)
        self.event = baker.make(
            Event,
            group=self.group,
            name="Build <together> & learn",
            description="<p>Learn &amp; build.</p><script>private_script()</script>",
            start_datetime=timezone.now() + timedelta(days=2),
            end_datetime=timezone.now() + timedelta(days=2, hours=2),
            location_name="Public venue",
            location_address="123 Example Street, Spokane, WA 99201",
            url="https://www.meetup.com/example/events/123/",
            event_schema_verified=True,
        )

    def page(self, url, **headers):
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 200)
        return response, BeautifulSoup(response.content, "html.parser")

    def payload(self, page):
        return json.loads(page.select_one("[data-st-page-metadata]").string)

    @override_settings(SEO_INDEXING_ENABLED=False)
    def test_safe_defaults_and_staging_sitemap(self):
        response, page = self.page(reverse("web:index"))
        self.assertEqual(page.select_one("meta[name=robots]")["content"], "noindex, follow")
        self.assertEqual(response["X-Robots-Tag"], "noindex, follow")
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /")
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertNotIn(b"<loc>", sitemap.content)

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_public_metadata_and_host_independence(self):
        response, page = self.page(self.event.get_absolute_url())
        self.assertNotIn("X-Robots-Tag", response)
        self.assertIn(self.event.name, page.title.string)
        self.assertEqual(page.select_one("meta[name=description]")["content"], "Learn & build.")
        self.assertNotIn("private_script", self.payload(page)["description"])
        self.assertEqual(
            page.select_one("link[rel=canonical]")["href"],
            "https://www.spokanetech.org" + self.event.get_absolute_url(),
        )
        self.assertTrue(
            page.select_one('meta[property="og:image"]')["content"].startswith("https://www.spokanetech.org/static/")
        )
        response, other = self.page(self.group.get_absolute_url())
        self.assertIn(self.group.name, other.title.string)
        self.assertNotEqual(page.title.string, other.title.string)

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_utility_filters_calendar_and_disabled_groups_stay_out_of_search(self):
        self.group.enabled = False
        self.group.save()
        for url in [
            self.group.get_absolute_url(),
            self.event.get_absolute_url(),
            "/host/",
            "/calendar/0/0/",
            "/events/list?group_id=1",
            "/events/li",
        ]:
            with self.subTest(url=url):
                self.assertIn("noindex", self.client.get(url)["X-Robots-Tag"])
        self.assertIn("noindex", self.client.get("/events/999999/")["X-Robots-Tag"])
        _, fragment = self.page(self.group.get_absolute_url(), HTTP_HX_REQUEST="true")
        self.assertFalse(self.payload(fragment)["public"])
        self.assertEqual(self.payload(fragment)["robots"], "noindex, follow")
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Disallow: /console/")
        self.assertContains(robots, "Sitemap: https://www.spokanetech.org/sitemap.xml")

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_campaign_canonical_and_analytics_do_not_accept_arbitrary_queries(self):
        response, page = self.page(
            "/events/list?utm_source=partner&utm_campaign=weekly&utm_medium=organic_social&token=private"
        )
        state = self.payload(page)
        self.assertEqual(state["canonical"], "https://www.spokanetech.org/events/list")
        self.assertNotIn("token", state["analytics_location"])
        self.assertNotIn("private", state["analytics_location"])
        self.assertIn("utm_source=partner", state["analytics_location"])
        self.assertIn("noindex", response["X-Robots-Tag"])
        response, page = self.page("/events/list?utm_source=partner")
        self.assertNotIn("X-Robots-Tag", response)

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_full_htmx_and_history_restore_share_metadata_and_vary(self):
        _, full = self.page(self.event.get_absolute_url())
        response, fragment = self.page(self.event.get_absolute_url(), HTTP_HX_REQUEST="true")
        self.assertEqual(self.payload(full), self.payload(fragment))
        self.assertIsNone(fragment.html)
        self.assertIn("HX-Request", response["Vary"])
        self.assertEqual(int(response["Content-Length"]), len(response.content))
        self.assertIn("HX-History-Restore-Request", response["Vary"])
        self.assertIn("noindex", response["X-Robots-Tag"])
        response, restored = self.page(
            self.event.get_absolute_url(), HTTP_HX_REQUEST="true", HTTP_HX_HISTORY_RESTORE_REQUEST="true"
        )
        self.assertIsNotNone(restored.html)
        self.assertEqual(self.payload(full), self.payload(restored))

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_index_alias_redirect_preserves_campaign_and_detail_links_do_not_redirect(self):
        response = self.client.get("/index/?utm_source=partner")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/?utm_source=partner")
        self.assertEqual(reverse("web:index"), "/")
        _, homepage = self.page("/")
        _, alias = self.page("/index/", HTTP_HX_REQUEST="true")
        self.assertEqual(self.payload(alias), self.payload(homepage))
        self.page(self.event.get_absolute_url())
        self.page(reverse("web:get_events"))  # Existing directory aliases retain compatibility.

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_sitemap_advertises_only_canonical_enabled_future_records(self):
        disabled = baker.make("web.TechGroup", enabled=False)
        hidden = baker.make(Event, group=disabled, start_datetime=self.event.start_datetime)
        past = baker.make(Event, start_datetime=timezone.now() - timedelta(days=1))
        cancelled = baker.make(Event, start_datetime=self.event.start_datetime, status=Event.Status.CANCELLED)
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        urls = {node.text for node in root.findall("{*}url/{*}loc")}
        self.assertIn("https://www.spokanetech.org" + self.event.get_absolute_url(), urls)
        self.assertIn("https://www.spokanetech.org" + self.group.get_absolute_url(), urls)
        for path in [
            hidden.get_absolute_url(),
            past.get_absolute_url(),
            cancelled.get_absolute_url(),
            disabled.get_absolute_url(),
            "/calendar/0/0/",
            "/index/",
        ]:
            self.assertNotIn("https://www.spokanetech.org" + path, urls)
        self.assertNotIn(b"<lastmod>", response.content)

    def test_event_schema_is_reviewed_safe_complete_and_tracks_cancellation(self):
        self.event.name = "Unsafe </script><script>alert(1)</script>"
        self.event.save()
        _, page = self.page(self.event.get_absolute_url())
        scripts = page.select('script[type="application/ld+json"]')
        self.assertEqual(len(scripts), 1)
        data = json.loads(scripts[0].string)
        event = next(item for item in data if item["@type"] == "Event")
        self.assertEqual(event["name"], self.event.name)
        self.assertNotIn("offers", event)
        self.assertEqual(event["location"]["address"]["name"], self.event.location_address)
        self.assertRegex(event["startDate"], r"[+-]\d\d:\d\d$")
        self.assertNotIn("</script>", scripts[0].string)
        self.event.status = Event.Status.CANCELLED
        self.event.save()
        _, page = self.page(self.event.get_absolute_url())
        updated = next(
            item for item in json.loads(page.select_one("[data-st-schema]").string) if item["@type"] == "Event"
        )
        self.assertEqual(updated["eventStatus"], "https://schema.org/EventCancelled")
        self.assertEqual(updated["startDate"], event["startDate"])
        for changes in [{"event_schema_verified": False}, {"event_schema_verified": True, "location_address": ""}]:
            Event.objects.filter(pk=self.event.pk).update(**changes)
            _, page = self.page(self.event.get_absolute_url())
            self.assertFalse(any(item["@type"] == "Event" for item in self.payload(page)["structured_data"]))

    @patch("web.event_ingestion.queue_event_image")
    def test_source_change_requires_review_but_unchanged_poll_and_cancellation_do_not(self, queue):
        for data, complete, expected in [
            ({"name": self.event.name}, False, True),
            ({"status": "cancelled"}, False, True),
            ({"name": self.event.name, "location_name": "New venue", "location_address": "New address"}, True, False),
        ]:
            event, _ = save_source_event(self.group, data, existing_pk=self.event.pk, location_complete=complete)
            self.assertEqual(event.event_schema_verified, expected)

    @patch("web.event_ingestion.queue_event_image")
    def test_rescheduling_start_or_end_requires_schema_review(self, queue):
        for field in ("start_datetime", "end_datetime"):
            with self.subTest(field=field):
                Event.objects.filter(pk=self.event.pk).update(event_schema_verified=True)
                event, _ = save_source_event(
                    self.group,
                    {"name": self.event.name, field: getattr(self.event, field) + timedelta(hours=1)},
                    existing_pk=self.event.pk,
                )
                self.assertFalse(event.event_schema_verified)

    @override_settings(SEO_INDEXING_ENABLED=True)
    def test_guides_use_actual_enabled_groups_and_future_events(self):
        disabled = baker.make("web.TechGroup", enabled=False, name="Hidden group")
        past = baker.make(
            Event, group=self.group, name="Past test event", start_datetime=timezone.now() - timedelta(days=1)
        )
        for name in ["newcomer_guide", "community_guide"]:
            response, page = self.page(reverse("web:" + name))
            self.assertContains(response, self.group.name)
            self.assertContains(response, "Build &lt;together&gt; &amp; learn")
            self.assertNotContains(response, disabled.name)
            self.assertNotContains(response, past.name)
            self.assertEqual(len(page.select("h1")), 1)
            self.assertEqual(page.select_one("meta[name=robots]")["content"], "index, follow")

    @override_settings(SEO_INDEXING_ENABLED=True, GOOGLE_ANALYTICS_TAG_ID="G-EXAMPLE", GA4_MANUAL_PAGE_VIEWS=True)
    def test_ga_is_not_loaded_on_private_pages_and_manual_mode_disables_initial_auto_view(self):
        response, _ = self.page("/")
        self.assertContains(response, "send_page_view: false")
        self.assertContains(response, "G-EXAMPLE")
        response, _ = self.page("/host/")
        self.assertNotContains(response, "googletagmanager.com/gtag")

    @override_settings(PROMOTE_SITE_LINKS=True)
    @patch("web.utilities.notifiers.discord.generate_post_content", side_effect=ValueError)
    def test_promotion_keeps_rsvp_and_opt_in_discovery_and_never_posts(self, ai):
        notifier = DiscordNotifier("https://example.test/unused")
        payload = notifier.build_event_created_message(self.event)
        self.assertIn("utm_source=discord", payload["embeds"][0]["url"])
        self.assertIn(self.event.url, payload["content"])
        with self.settings(PROMOTE_SITE_LINKS=False):
            payload = notifier.build_event_created_message(self.event)
            self.assertEqual(payload["embeds"][0]["url"], self.event.url)
        self.assertIn("utm_source=partner", campaign_url(self.event.get_absolute_url(), "partner"))

    def test_preview_is_read_only_and_uses_database_events(self):
        baker.make(Event, group=self.group, start_datetime=self.event.start_datetime, url="", name="No RSVP link")
        output = StringIO()
        call_command("preview_growth_posts", source="partner", stdout=output)
        preview = json.loads(output.getvalue())
        self.assertEqual(len(preview), 1)
        self.assertEqual(preview[0]["name"], self.event.name)
        self.assertEqual(preview[0]["rsvp_url"], self.event.url)
        self.assertIn("utm_source=partner", preview[0]["discovery_url"])

    @patch("web.utilities.notifiers.discord.generate_post_content", side_effect=ValueError)
    def test_discord_omits_missing_optional_url_and_location(self, ai):
        self.event.url = ""
        self.event.location_name = ""
        notifier = DiscordNotifier("https://example.test/unused")
        for enabled in (False, True):
            with self.settings(PROMOTE_SITE_LINKS=enabled):
                for builder in (notifier.build_event_created_message, notifier.build_event_reminder_message):
                    with self.subTest(promotion=enabled, builder=builder.__name__):
                        payload = builder(self.event)
                        embed = payload["embeds"][0]
                        if enabled:
                            self.assertIn("www.spokanetech.org/events/", embed["url"])
                        else:
                            self.assertNotIn("url", embed)
                        self.assertNotIn("RSVP", payload["content"])
                        self.assertTrue(all(field["value"] for field in embed["fields"]))

    def test_public_origin_rejects_untrusted_or_incomplete_origins(self):
        for value in [
            "http://example.org",
            "https://user:password@example.org",
            "https://example.org/path",
            "//example.org",
        ]:
            with self.subTest(value=value), self.settings(PUBLIC_SITE_URL=value):
                with self.assertRaises(ImproperlyConfigured):
                    public_origin()

    @override_settings(
        SEO_VERIFIED_PROFILE_URLS=["/relative", "http://example.org/profile", "https://example.org/owned"]
    )
    def test_organization_uses_only_configured_https_profiles(self):
        _, page = self.page("/")
        organization = next(item for item in self.payload(page)["structured_data"] if item["@type"] == "Organization")
        self.assertEqual(organization["sameAs"], ["https://example.org/owned"])

    @override_settings(PROMOTE_SITE_LINKS=True)
    @patch("web.utilities.notifiers.discord.generate_post_content", return_value="Review this week's events. " * 200)
    def test_weekly_promotion_is_bounded_and_preserves_both_destinations(self, ai):
        baker.make(
            Event,
            group=self.group,
            start_datetime=self.event.start_datetime,
            name="Event with a long title " * 20,
            description="Description " * 300,
            url="https://www.meetup.com/example/events/456/",
            _quantity=30,
        )
        events = Event.objects.select_related("group").order_by("pk")
        payload = DiscordNotifier("https://example.test/unused").build_weekly_event_summary(events)
        fields = payload["embeds"][0]["fields"]
        self.assertLessEqual(len(payload["content"]), 2000)
        self.assertLessEqual(len(fields), 25)
        self.assertLessEqual(sum(len(item["name"]) + len(item["value"]) for item in fields), 5000)
        for item in fields:
            self.assertLessEqual(len(item["name"]), 256)
            self.assertLessEqual(len(item["value"]), 1024)
            self.assertIn("www.spokanetech.org/events/", item["value"])
            self.assertIn("www.meetup.com/", item["value"])
        self.assertIn("of 31 events", payload["content"])

    @override_settings(PROMOTE_SITE_LINKS=True)
    @patch("web.utilities.notifiers.linkedin.generate_post_content", return_value="Actual event summary. " * 200)
    def test_linkedin_preview_retains_rsvp_when_commentary_is_truncated(self, ai):
        client = LinkedInOrganizationClient(None, "urn:li:organization:example")
        commentary = client.build_event_commentary(self.event)
        self.assertLessEqual(len(commentary), 3000)
        self.assertIn("utm_source=linkedin", commentary)
        self.assertIn(self.event.url, commentary)
        with patch.object(client, "post_organization_post") as send:
            client.post_event(self.event)
            self.assertIn("www.spokanetech.org/events/", send.call_args.kwargs["article_url"])

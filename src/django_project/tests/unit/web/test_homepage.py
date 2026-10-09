"""Homepage data, navigation, and query regression coverage."""

import os
from datetime import datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker

from web.models import Event, TechGroup


class HomepageTests(TestCase):
    def setUp(self):
        self.url = reverse("web:index")
        self.now = datetime(2026, 1, 8, 18, 0, tzinfo=datetime_timezone.utc)
        self.group = baker.make("web.TechGroup", name="Local builders", enabled=True)
        self.other_group = baker.make("web.TechGroup", name="Other builders", enabled=True)
        self.disabled_group = baker.make("web.TechGroup", name="Disabled builders", enabled=False)
        self.tag = baker.make("web.Tag", value="Community topic")
        self.group.tags.add(self.tag)
        self.future = baker.make(
            "web.Event",
            name="Next gathering",
            group=self.group,
            start_datetime=self.now + timedelta(hours=8, minutes=30),
            location_name="Community space",
        )
        self.future.tags.add(self.tag)
        self.past = baker.make(
            "web.Event", name="Previous gathering", group=self.group, start_datetime=self.now - timedelta(days=1)
        )

    def get_home(self, **headers):
        with patch("web.views.timezone.now", return_value=self.now):
            return self.client.get(self.url, **headers)

    def test_initial_and_htmx_render_real_data_and_detail_links(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.get_home(**headers)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, self.future.name)
                self.assertContains(response, self.future.get_absolute_url())
                self.assertContains(response, self.group.get_absolute_url())
                self.assertContains(response, self.tag.value)
                self.assertNotContains(response, self.past.name)
                self.assertNotContains(response, self.disabled_group.name)
                self.assertContains(response, "<h1 ", count=1)
                self.assertNotContains(response, 'hx-trigger="load"')
                if headers:
                    self.assertNotContains(response, "<html")
                else:
                    self.assertContains(response, "<html")

    def test_upcoming_order_limit_boundary_and_total_counts(self):
        later = baker.make("web.Event", group=self.group, start_datetime=self.now + timedelta(days=2), _quantity=4)
        boundary = baker.make("web.Event", group=None, start_datetime=self.now)
        response = self.get_home()
        displayed = response.context["upcoming_events"]
        self.assertEqual([event.pk for event in displayed], [boundary.pk, self.future.pk, later[0].pk, later[1].pk])
        self.assertEqual(response.context["upcoming_event_count"], 6)
        self.assertEqual(response.context["active_group_count"], 2)
        counts = {group.pk: group.upcoming_event_count for group in response.context["homepage_groups"]}
        self.assertEqual(counts, {self.group.pk: 5, self.other_group.pk: 0})

    def test_empty_events_and_groups_are_usable(self):
        Event.objects.all().delete()
        TechGroup.objects.all().update(enabled=False)
        response = self.get_home()
        self.assertContains(response, "There are no upcoming events listed right now.")
        self.assertContains(response, "Local groups will appear here")
        self.assertContains(response, reverse("web:event_calendar", kwargs={"year": 0, "month": 0}))
        self.assertContains(response, reverse("web:get_techgroups", kwargs={"display": "list"}))
        self.assertEqual(response.context["upcoming_event_count"], 0)
        self.assertEqual(response.context["active_group_count"], 0)
        self.assertNotContains(response, 'class="st-tag"')

    def test_only_live_topics_are_used_and_deduplicated(self):
        hidden_tag = baker.make("web.Tag", value="Inactive topic")
        self.disabled_group.tags.add(hidden_tag)
        self.past.tags.add(hidden_tag)
        baker.make("web.Tag", value="Unused topic")
        response = self.get_home()
        self.assertEqual([tag.pk for tag in response.context["community_tags"]], [self.tag.pk])

    def test_dates_use_spokane_timezone_and_semantic_timestamps(self):
        response = self.get_home()
        self.assertContains(response, "Thu, Jan 8, 2026")
        self.assertContains(response, "6:30 PM PST")
        self.assertContains(response, 'datetime="2026-01-08T18:30:00-08:00"')
        self.future.start_datetime = datetime(2026, 7, 9, 1, 30, tzinfo=datetime_timezone.utc)
        self.future.save()
        response = self.get_home()
        self.assertContains(response, "6:30 PM PDT")
        self.assertContains(response, 'datetime="2026-07-08T18:30:00-07:00"')

    def test_authenticated_user_sees_same_public_homepage(self):
        self.client.force_login(baker.make("auth.User"))
        response = self.get_home()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.future.name)
        self.assertEqual(response.context["active_group_count"], 2)

    def test_legacy_icons_preserve_classes_without_rendering_stored_html(self):
        self.group.icon = (
            '<i class="fa-brands fa-python arbitrary-class" onclick="unsafe()"></i><script>unsafe()</script>'
        )
        self.group.save()
        self.other_group.icon = "fas fa-users"
        self.other_group.save()
        response = self.get_home()
        self.assertContains(response, 'class="fa-brands fa-python"')
        self.assertContains(response, 'class="fas fa-users"')
        self.assertNotContains(response, "unsafe()")
        self.assertNotContains(response, "arbitrary-class")

    @override_settings(DEBUG=False)
    def test_queries_stay_bounded_as_homepage_data_grows(self):
        with CaptureQueriesContext(connection) as small:
            self.get_home()
        for index in range(8):
            group = baker.make("web.TechGroup", name=f"A local group {index}", enabled=True)
            group.tags.add(self.tag)
            event = baker.make("web.Event", group=group, start_datetime=self.now + timedelta(hours=index))
            event.tags.add(self.tag)
        with CaptureQueriesContext(connection) as large:
            response = self.get_home()
        self.assertEqual(len(response.context["upcoming_events"]), 4)
        self.assertEqual(len(response.context["homepage_groups"]), 10)
        self.assertContains(response, self.group.get_absolute_url())
        self.assertContains(response, self.other_group.get_absolute_url())
        self.assertNotContains(response, self.disabled_group.name)
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 7)

    @override_settings(COMMUNITY_DISCORD_URL="", COMMUNITY_SOCIAL_LINKS=())
    def test_unconfigured_community_links_are_omitted(self):
        response = self.get_home()
        self.assertNotContains(response, "discord.gg")
        self.assertNotContains(response, "Join Discord")
        self.assertContains(response, "Explore Upcoming Events")
        self.assertContains(response, reverse("web:get_events", kwargs={"display": "list"}))

    def test_global_navigation_routes_render(self):
        for name, kwargs in (
            ("web:index", {}),
            ("web:about", {}),
            ("web:develop", {}),
            ("web:event_calendar", {"year": 0, "month": 0}),
            ("web:get_events", {"display": "list"}),
            ("web:get_techgroups", {"display": "list"}),
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, kwargs=kwargs)).status_code, 200)

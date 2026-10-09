"""Event directory rendering, compatibility, and related-data query coverage."""

import os
from datetime import timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker


class EventDirectoryTests(TestCase):
    def setUp(self):
        self.url = reverse("web:get_events", kwargs={"display": "list"})
        self.group = baker.make("web.TechGroup", name="Local builders")
        self.tag = baker.make("web.Tag", value="Python")
        start = timezone.now() + timedelta(days=1)
        self.event = baker.make(
            "web.Event",
            name="Build together",
            group=self.group,
            start_datetime=start,
            end_datetime=start + timedelta(hours=2),
            location_name="Community workshop",
            image="tech_events/workshop.jpg",
        )
        self.event.tags.add(self.tag)
        self.past = baker.make("web.Event", name="Past workshop", start_datetime=start - timedelta(days=2))

    def test_full_and_htmx_render_event_information(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                self.assertEqual(response.status_code, 200)
                for value in (
                    self.event.name,
                    self.group.name,
                    self.event.get_absolute_url(),
                    self.event.image.url,
                    self.tag.value,
                    self.event.location_name,
                    "1 upcoming event",
                    '<h1 id="event-directory-title">',
                    '<h2><a class="st-card-link"',
                    'class="st-date-badge"',
                ):
                    self.assertContains(response, value)
                self.assertNotContains(response, self.past.name)
                self.assertNotContains(response, 'hx-trigger="load"')
                self.assertEqual(response["X-Initialize-Tables"], "initialize-tables")
                if headers:
                    self.assertNotContains(response, "<html")
                else:
                    self.assertTemplateUsed(response, "base.htm")

    def test_ordering_default_route_and_existing_filters(self):
        later = baker.make(
            "web.Event", name="Later meetup", start_datetime=self.event.start_datetime + timedelta(days=1)
        )
        response = self.client.get(reverse("web:get_events"))
        self.assertContains(response, "2 upcoming events")
        self.assertLess(response.content.index(self.event.name.encode()), response.content.index(later.name.encode()))
        response = self.client.get(self.url, {"group_id": self.group.pk}, HTTP_HX_REQUEST="true")
        self.assertContains(response, self.event.name)
        self.assertNotContains(response, later.name)
        self.assertContains(response, "1 upcoming event")

    def test_empty_state_and_minimal_display_are_preserved(self):
        response = self.client.get(self.url, {"name": "Missing meetup"})
        self.assertContains(response, "0 upcoming events")
        self.assertContains(response, "No upcoming events match this list.")
        self.assertContains(response, reverse("web:get_techgroups", kwargs={"display": "list"}))
        response = self.client.get(reverse("web:get_events", kwargs={"display": "li"}), HTTP_HX_REQUEST="true")
        self.assertContains(response, self.event.name)
        self.assertNotContains(response, "st-event-directory-grid")

    def test_missing_group_image_and_location_use_existing_fallback(self):
        self.event.group = None
        self.event.image = None
        self.event.location_name = ""
        self.event.location_address = "123 Main Street"
        self.event.save()
        response = self.client.get(self.url)
        self.assertContains(response, "SpokaneTech")
        self.assertContains(response, "123 Main Street")
        self.assertContains(response, self.event.name)

    @override_settings(DEBUG=False)
    def test_related_data_query_count_is_constant(self):
        with CaptureQueriesContext(connection) as small:
            self.client.get(self.url)
        for index in range(8):
            group = baker.make("web.TechGroup", name=f"Organizer {index}")
            event = baker.make("web.Event", group=group, start_datetime=self.event.start_datetime)
            event.tags.add(self.tag)
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(self.url)
        self.assertContains(response, "9 upcoming events")
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 2)

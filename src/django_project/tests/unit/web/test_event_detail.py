"""Event detail rendering, real content, Pacific times, and optional fields."""

import os
from datetime import datetime, timezone

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.test import TestCase
from model_bakery import baker


class EventDetailTests(TestCase):
    def setUp(self):
        self.group = baker.make("web.TechGroup", name="Community builders")
        self.event = baker.make(
            "web.Event",
            name="Build together",
            group=self.group,
            start_datetime=datetime(2026, 10, 21, 0, 30, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc),
            description="<p>Learn <strong>together</strong>.</p>",
            location_name="Community room",
            location_address="123 Main Street",
            map_link="https://example.com/map",
            url="https://example.com/event",
            image="tech_events/community.jpg",
        )
        self.event.tags.add(baker.make("web.Tag", value="Development"))
        self.url = self.event.get_absolute_url()

    def test_full_and_htmx_pages_render_real_details(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "web/partials/detail/event.htm")
                for text in (
                    "<h1>Build together</h1>",
                    self.group.name,
                    self.group.get_absolute_url(),
                    self.event.description,
                    self.event.image.url,
                    "Tuesday, Oct 20, 2026",
                    "5:30 PM PDT",
                    "7:30 PM PDT",
                    "Community room",
                    "123 Main Street",
                    self.event.map_link,
                    self.event.url,
                    "Development",
                ):
                    self.assertContains(response, text)
                self.assertNotContains(response, 'href="#"')
                self.assertNotContains(response, 'href=""')
                self.assertNotContains(response, 'hx-trigger="load"')
                self.assertContains(response, 'target="_blank" rel="noopener"')
                html = response.content.decode()
                self.assertLess(html.index(self.event.description), html.index('aria-label="Event topics"'))

    def test_missing_optional_fields_have_no_empty_links_or_sections(self):
        self.event.group = None
        self.event.image = ""
        self.event.description = ""
        self.event.end_datetime = None
        self.event.location_name = ""
        self.event.location_address = ""
        self.event.map_link = ""
        self.event.url = ""
        self.event.tags.clear()
        self.event.save()
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertContains(response, "No description has been added")
        for text in (
            "Hosted by",
            "Meet the host",
            "RSVP",
            "<dt>Where</dt>",
            'aria-label="Event topics"',
            "<img",
            'href=""',
        ):
            self.assertNotContains(response, text)

    def test_address_without_map_and_cross_day_end_are_visible(self):
        self.event.location_name = ""
        self.event.map_link = ""
        self.event.end_datetime = datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc)
        self.event.save()
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertContains(response, self.event.location_address)
        self.assertContains(response, "(Oct 21, 2026)")
        self.assertNotContains(response, "View map")

    def test_relations_are_loaded_in_two_queries(self):
        from web.views import TechEventView

        with self.assertNumQueries(2):
            event = TechEventView().get_queryset().get(pk=self.event.pk)
            self.assertEqual(event.group.name, self.group.name)
            self.assertEqual([tag.value for tag in event.tags.all()], ["Development"])

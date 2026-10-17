"""Group detail content, event ordering, navigation, and query coverage."""

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


class GroupDetailTests(TestCase):
    def setUp(self):
        self.group = baker.make(
            "web.TechGroup",
            name="Local makers",
            description="<p>Learn <strong>together</strong> and build.</p>",
            icon='<i class="fab fa-python" onclick="unsafe()"></i>',
        )
        self.topic = baker.make("web.Tag", value="Development")
        self.group.tags.add(self.topic)
        self.link = baker.make("web.Link", name="Group website", url="https://example.com/community")
        self.group.links.add(self.link)
        now = timezone.now()
        self.upcoming = baker.make(
            "web.Event",
            group=self.group,
            name="Next workshop",
            start_datetime=now + timedelta(days=1),
            location_name="Community space",
            location_address="123 Main Street",
            url="https://example.com/next",
        )
        self.upcoming.tags.add(self.topic)
        self.past = baker.make(
            "web.Event",
            group=self.group,
            name="Previous workshop",
            start_datetime=now - timedelta(days=1),
            url="https://example.com/previous",
        )
        self.url = self.group.get_absolute_url()

    def test_full_and_htmx_keep_content_and_real_links(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                for value in (
                    "<h1>Local makers</h1>",
                    "<strong>together</strong>",
                    'class="fab fa-python"',
                    self.topic.value,
                    self.link.name,
                    self.link.url,
                    self.upcoming.name,
                    self.upcoming.get_absolute_url(),
                    self.past.name,
                    self.past.get_absolute_url(),
                    self.upcoming.url,
                    self.past.url,
                    "123 Main Street",
                    "Community space",
                    "1 upcoming event",
                    "1 past event",
                    "Upcoming events",
                    "Past events",
                ):
                    self.assertContains(response, value)
                self.assertNotContains(response, "unsafe()")
                self.assertNotContains(response, 'hx-trigger="load"')
                if headers:
                    self.assertNotContains(response, "<html")
                else:
                    self.assertTemplateUsed(response, "base.htm")

    def test_event_sections_have_correct_members_and_order(self):
        later = baker.make(
            "web.Event", group=self.group, start_datetime=self.upcoming.start_datetime + timedelta(days=1)
        )
        earlier = baker.make("web.Event", group=self.group, start_datetime=self.past.start_datetime - timedelta(days=1))
        unrelated = baker.make("web.Event", start_datetime=self.upcoming.start_datetime)
        response = self.client.get(self.url)
        self.assertEqual([event.pk for event in response.context["upcoming_events"]], [self.upcoming.pk, later.pk])
        self.assertEqual([event.pk for event in response.context["past_events"]], [self.past.pk, earlier.pk])
        self.assertNotContains(response, unrelated.name)

    def test_missing_information_and_empty_sections(self):
        self.group.description = ""
        self.group.icon = ""
        self.group.save()
        self.group.links.clear()
        self.group.event_set.all().delete()
        response = self.client.get(self.url)
        self.assertContains(response, "This group hasn't added a description yet.")
        self.assertContains(response, "No upcoming events are listed yet.")
        self.assertContains(response, "No past events are listed yet.")
        self.assertNotContains(response, "Connect with the group")
        self.assertContains(response, "st-group-about-only")

    def test_stored_image_and_missing_group_are_handled(self):
        self.group.image = "techgroups/makers.png"
        self.group.save()
        response = self.client.get(self.url)
        self.assertContains(response, self.group.image.url)
        self.assertEqual(self.client.get(reverse("web:get_techgroup", kwargs={"pk": 999999})).status_code, 404)

    @override_settings(DEBUG=False)
    def test_queries_do_not_grow_with_events_and_links(self):
        with CaptureQueriesContext(connection) as small:
            self.client.get(self.url)
        for index in range(8):
            event = baker.make("web.Event", group=self.group, start_datetime=self.upcoming.start_datetime)
            event.tags.add(self.topic)
            self.group.links.add(baker.make("web.Link", name=f"Link {index}"))
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(self.url)
        self.assertContains(response, "9 upcoming events")
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 5)

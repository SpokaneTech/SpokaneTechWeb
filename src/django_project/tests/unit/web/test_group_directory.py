"""Group directory data, initial rendering, filtering, and query regression coverage."""

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


class GroupDirectoryTests(TestCase):
    def setUp(self):
        self.url = reverse("web:get_techgroups", kwargs={"display": "list"})
        self.group = baker.make(
            "web.TechGroup",
            name="Local builders",
            description="<p>Learn and build <strong>together</strong>.</p>",
            icon='<i class="fa-brands fa-python" onclick="unsafe()"></i>',
            enabled=True,
        )
        self.disabled = baker.make("web.TechGroup", name="Disabled builders", enabled=False)
        self.topic = baker.make("web.Tag", value="Development")
        self.group.tags.add(self.topic)
        now = timezone.now()
        baker.make("web.Event", group=self.group, start_datetime=now + timedelta(days=1), _quantity=2)
        baker.make("web.Event", group=self.group, start_datetime=now - timedelta(days=1))

    def test_full_and_htmx_directory_render_real_data(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<h1 id="directory-title">', count=1)
                self.assertContains(response, self.group.name)
                self.assertContains(response, self.group.get_absolute_url())
                self.assertContains(response, "Learn and build together.")
                self.assertContains(response, "2 upcoming events")
                self.assertContains(response, "1 local group")
                self.assertContains(response, self.topic.value)
                self.assertContains(response, 'class="fa-brands fa-python"')
                self.assertNotContains(response, "unsafe()")
                self.assertNotContains(response, self.disabled.name)
                self.assertNotContains(response, 'hx-trigger="load"')
                if headers:
                    self.assertEqual(response["X-Initialize-Tables"], "initialize-tables")
                    self.assertNotContains(response, "<html")
                else:
                    self.assertNotIn("X-Initialize-Tables", response.headers)
                    self.assertTemplateUsed(response, "base.htm")

    def test_default_route_renders_directory(self):
        response = self.client.get(reverse("web:get_techgroups"))
        self.assertContains(response, "Spokane's tech groups")
        self.assertContains(response, self.group.name)

    def test_description_entities_and_paragraphs_render_as_safe_plain_text(self):
        self.group.description = "<p>Learn &amp; build.</p><p>Meet friends.</p><script>unsafe()</script>"
        self.group.save()
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                self.assertContains(response, "Learn &amp; build. Meet friends.")
                self.assertNotContains(response, "&amp;amp;")
                self.assertNotContains(response, "unsafe()")

    def test_empty_directory_has_helpful_state(self):
        self.group.enabled = False
        self.group.save()
        response = self.client.get(self.url)
        self.assertContains(response, "0 local groups")
        self.assertContains(response, "There are no groups listed here yet.")
        self.assertContains(response, reverse("web:about"))

    def test_existing_filters_and_counts_are_preserved(self):
        another = baker.make("web.TechGroup", name="Other builders", enabled=True)
        another.tags.add(self.topic)
        second_topic = baker.make("web.Tag", value="Community")
        self.group.tags.add(second_topic)
        response = self.client.get(self.url, {"name": self.group.name}, HTTP_HX_REQUEST="true")
        self.assertContains(response, self.group.name)
        self.assertNotContains(response, another.name)
        response = self.client.get(self.url, {"tags__value__in": "Development,Community", "distinct": "true"})
        self.assertContains(response, "2 upcoming events", count=1)
        self.assertContains(response, "2 local groups")

    @override_settings(DEBUG=False)
    def test_query_count_does_not_grow_with_groups_and_tags(self):
        with CaptureQueriesContext(connection) as small:
            self.client.get(self.url)
        for index in range(8):
            group = baker.make("web.TechGroup", name=f"Group {index}", enabled=True)
            group.tags.add(self.topic)
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(self.url)
        self.assertContains(response, "9 local groups")
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 2)

    def test_authenticated_user_can_render_directory(self):
        self.client.force_login(baker.make("auth.User"))
        response = self.client.get(self.url)
        self.assertContains(response, self.group.name)

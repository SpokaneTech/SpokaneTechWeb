"""Full directory shells must never include themselves through helper context."""

import os
from datetime import timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker


class DirectoryTemplateTests(TestCase):
    def test_full_shells_ignore_self_referencing_partial_context(self):
        for name, heading in (("events", "Upcoming events"), ("groups", "Spokane's tech groups")):
            with self.subTest(name=name):
                template = f"web/full/list/{name}.html"
                html = render_to_string(template, {"htmx_template_name": template, "queryset": []})
                self.assertIn(heading, html)
                self.assertEqual(html.count('<main id="body_main"'), 1)
                self.assertEqual(html.count("<!DOCTYPE html>"), 1)

    def test_direct_and_htmx_requests_preserve_directory_content(self):
        group = baker.make("web.TechGroup", name="Template regression group", enabled=True)
        event = baker.make(
            "web.Event",
            name="Template regression event",
            group=group,
            start_datetime=timezone.now() + timedelta(days=1),
        )
        for route, name, label in (
            ("get_events", event.name, "event-directory-title"),
            ("get_techgroups", group.name, "directory-title"),
        ):
            url = reverse(f"web:{route}", kwargs={"display": "list"})
            for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
                with self.subTest(route=route, headers=headers):
                    response = self.client.get(url, **headers)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, name)
                    self.assertContains(response, f'<h1 id="{label}"', count=1)
                    self.assertContains(response, "<!DOCTYPE html>", count=0 if headers else 1)

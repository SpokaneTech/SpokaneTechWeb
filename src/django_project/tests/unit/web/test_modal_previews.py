"""Shared event/group modal rendering and preserved navigation."""

import os
from datetime import datetime, timezone

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.test import TestCase
from django.urls import reverse
from model_bakery import baker


class ModalPreviewTests(TestCase):
    def setUp(self):
        self.group = baker.make(
            "web.TechGroup",
            name="Community builders",
            image="techgroups/logo.png",
            description='<p>Build together.</p><img src="/embedded-group.png">',
        )
        self.event = baker.make(
            "web.Event",
            group=self.group,
            name="Meet and build",
            start_datetime=datetime(2026, 10, 20, 18, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 10, 20, 19, tzinfo=timezone.utc),
            location_name="",
            location_address="123 Main Street",
            map_link="",
            image="tech_events/photo.png",
            description='<p>Learn together.</p><img src="/embedded-event.png">',
            url="https://example.com/event",
        )
        tag = baker.make("web.Tag", value="Development")
        self.event.tags.add(tag)
        self.group.tags.add(tag)

    def test_event_preview_uses_same_responsive_template_for_all_clients(self):
        url = reverse("web:techevent_modal", kwargs={"pk": self.event.pk})
        for agent in ("Desktop browser", "Mobile browser"):
            with self.subTest(agent=agent):
                response = self.client.get(url, HTTP_HX_REQUEST="true", HTTP_USER_AGENT=agent)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "core/partials/modal_swap.htm")
                self.assertTemplateUsed(response, "web/partials/modal/event_information.htm")
                for value in (
                    self.event.name,
                    self.group.name,
                    "123 Main Street",
                    "11:00 AM PDT",
                    "12:00 PM PDT",
                    "Learn together.",
                    "Development",
                    self.event.url,
                    self.event.get_absolute_url(),
                ):
                    self.assertContains(response, value)
                self.assertContains(response, 'id="generic_modal_label"')
                self.assertContains(response, 'data-bs-dismiss="modal"')
                self.assertContains(
                    response, f'href="{self.event.get_absolute_url()}" hx-get="{self.event.get_absolute_url()}"'
                )
                self.assertNotContains(response, 'href=""')
                self.assertNotContains(response, "<img")
                self.assertNotContains(response, "modal-text-mobile")

    def test_map_is_available_without_hiding_plain_address(self):
        self.event.map_link = "https://example.com/map"
        self.event.save()
        response = self.client.get(reverse("web:techevent_modal", kwargs={"pk": self.event.pk}), HTTP_HX_REQUEST="true")
        self.assertContains(response, self.event.location_address)
        self.assertContains(response, self.event.map_link)
        self.assertContains(response, "View map")

    def test_group_preview_retains_description_links_and_details(self):
        link = baker.make("web.Link", name="Community website", url="https://example.com/community")
        self.group.links.add(link)
        response = self.client.get(reverse("web:techgroup_modal", kwargs={"pk": self.group.pk}), HTTP_HX_REQUEST="true")
        for value in (
            self.group.name,
            "Build together.",
            "Development",
            link.name,
            link.url,
            self.group.get_absolute_url(),
        ):
            self.assertContains(response, value)
        self.assertTemplateUsed(response, "core/partials/modal_swap.htm")
        self.assertNotContains(response, 'href=""')
        self.assertNotContains(response, "<img")

    def test_event_without_optional_data_and_non_htmx_requests(self):
        self.event.group = None
        self.event.end_datetime = None
        self.event.description = ""
        self.event.save()
        url = reverse("web:techevent_modal", kwargs={"pk": self.event.pk})
        response = self.client.get(url, HTTP_HX_REQUEST="true")
        self.assertContains(response, self.event.name)
        self.assertNotContains(response, "Hosted by")
        self.assertNotContains(response, "About this event")
        self.assertEqual(self.client.get(url).status_code, 400)

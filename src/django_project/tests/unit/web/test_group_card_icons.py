"""Stored group icons render without view-specific queryset preparation."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.test import TestCase
from django.urls import reverse
from model_bakery import baker


class GroupCardIconTests(TestCase):
    def test_full_and_htmx_lists_render_safe_legacy_and_class_only_icons(self):
        legacy = baker.make(
            "web.TechGroup",
            name="Legacy icon group",
            enabled=True,
            icon='<i class="fab fa-python" onclick="unsafe()"></i>',
        )
        bare = baker.make("web.TechGroup", name="Class icon group", enabled=True, icon="fa-solid fa-code")
        fallback = baker.make("web.TechGroup", name="Fallback group", enabled=True, icon="")
        image = baker.make(
            "web.TechGroup", name="Image group", enabled=True, image="techgroups/logo.png", icon="fas fa-star"
        )
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(reverse("web:get_techgroups", kwargs={"display": "list"}), **headers)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="fab fa-python"')
                self.assertContains(response, 'class="fa-solid fa-code"')
                self.assertContains(response, "<span>F</span>")
                self.assertContains(response, image.image.url)
                self.assertNotContains(response, 'class="fas fa-star"')
                self.assertNotContains(response, "unsafe()")
                for group in (legacy, bare, fallback, image):
                    self.assertContains(response, group.get_absolute_url())

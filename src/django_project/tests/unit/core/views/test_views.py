import os
from pathlib import Path

import django
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

BASE_DIR: Path = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


class RobotsTxtTests(TestCase):
    def test_get(self) -> None:
        response: HttpResponse = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/plain")
        self.assertTrue(response.content.startswith(b"User-Agent: *\n"))

    def test_post_disallowed(self) -> None:
        response: HttpResponse = self.client.post("/robots.txt")
        self.assertEqual(response.status_code, 405)


class TestHostView(TestCase):

    def test_get(self) -> None:
        """verify call to HostView view"""
        response: HttpResponse = self.client.get(reverse("host"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/host_info.html")

    def test_post(self) -> None:
        """verify call to HostView view"""
        response: HttpResponse = self.client.post(reverse("host"))
        self.assertEqual(response.status_code, 405)

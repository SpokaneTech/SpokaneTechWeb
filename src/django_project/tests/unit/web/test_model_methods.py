import os
import random
from pathlib import Path

import django
from django.test import TestCase
from django.urls import reverse

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")

django.setup()
from model_bakery import baker


class EventMethodTests(TestCase):
    """test model methods on Event"""

    def test_str(self):
        """verify __str__ method returns expected value"""
        value = "some_name"
        row = baker.make("web.Event", name=value)
        self.assertEqual(str(row), value)

    def test_get_absolute_url(self):
        """verity the get_absolute_url method returns the expected value"""
        row = baker.make("web.Event")
        expected_url = reverse("web:get_event", kwargs={"pk": row.pk})
        self.assertEqual(row.get_absolute_url(), expected_url)


class LinkMethodTests(TestCase):
    """test model methods on Link"""

    def test_str(self):
        """verify __str__ method returns expected value"""
        value = "http://some_url"
        row = baker.make("web.Link", url=value)
        self.assertEqual(str(row), value)


class SocialPlatformMethodTests(TestCase):
    """test model methods on SocialPlatform"""

    def test_str(self):
        """verify __str__ method returns expected value"""
        value = "some_name"
        row = baker.make("web.SocialPlatform", name=value)
        self.assertEqual(str(row), value)


class TagMethodTests(TestCase):
    """test model methods on Tag"""

    def test_str(self):
        """verify __str__ method returns expected value"""
        value = "some_tag"
        row = baker.make("web.Tag", value=value)
        self.assertEqual(str(row), value)


class TechGroupMethodTests(TestCase):
    """test model methods on TechGroup"""

    def test_str(self):
        """verify __str__ method returns expected value"""
        value = "some_name"
        row = baker.make("web.TechGroup", name=value)
        self.assertEqual(str(row), value)

    def test_get_absolute_url(self):
        """verity the get_absolute_url method returns the expected value"""
        row = baker.make("web.TechGroup")
        expected_url = reverse("web:get_techgroup", kwargs={"pk": row.pk})
        self.assertEqual(row.get_absolute_url(), expected_url)

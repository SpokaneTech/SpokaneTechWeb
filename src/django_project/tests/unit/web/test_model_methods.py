import os
import random
from pathlib import Path

import django
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

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

    def test_get_upcoming_events(self):
        """verify get_upcoming_events method returns expected value"""
        group = baker.make("web.TechGroup")
        past_events = baker.make(
            "web.Event",
            group=group,
            start_datetime=timezone.now() - timezone.timedelta(days=1),
            _quantity=3,
        )
        future_events = baker.make(
            "web.Event",
            group=group,
            start_datetime=timezone.now() + timezone.timedelta(days=1),
            _quantity=3,
        )
        upcoming = group.get_upcoming_events()
        self.assertEqual(len(upcoming), len(future_events))
        for event in future_events:
            self.assertIn(event, upcoming)
        for event in past_events:
            self.assertNotIn(event, upcoming)

    def test_get_upcoming_events_with_no_events(self):
        """verify get_upcoming_events method returns expected value when their are no upcoming events"""
        group = baker.make("web.TechGroup")
        past_events = baker.make(
            "web.Event",
            group=group,
            start_datetime=timezone.now() - timezone.timedelta(days=1),
            _quantity=3,
        )
        upcoming = group.get_upcoming_events()
        self.assertEqual(len(upcoming), 0)
        for event in past_events:
            self.assertNotIn(event, upcoming)

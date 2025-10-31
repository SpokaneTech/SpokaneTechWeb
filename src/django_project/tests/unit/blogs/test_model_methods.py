import os
import random
from pathlib import Path
from typing import Any

import django
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

django.setup()
from model_bakery import baker


class BlogPlatformMethodTests(TestCase):
    """test model methods on BlogPlatform"""

    def test_str(self) -> None:
        """verify __str__ method returns expected value"""
        value = "some_name"
        row: Any = baker.make("blogs.BlogPlatform", name=value)
        self.assertEqual(str(row), value)


class BlogPostMethodTests(TestCase):
    """test model methods on BlogPost"""

    def test_str(self) -> None:
        """verify __str__ method returns expected value"""
        value = "some_name"
        row: Any = baker.make("blogs.BlogPost", title=value)
        self.assertEqual(str(row), value)


class BlogSeriesMethodTests(TestCase):
    """test model methods on BlogSeries"""

    def test_str(self) -> None:
        """verify __str__ method returns expected value"""
        value = "some_name"
        row: Any = baker.make("blogs.BlogSeries", name=value)
        self.assertEqual(str(row), value)

import os
from datetime import timedelta
from pathlib import Path

import django
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")

django.setup()
from model_bakery import baker


class TestBlogPostListView(TestCase):
    def setUp(self):
        super(TestBlogPostListView, self).setUp()
        self.instance = baker.make("blogs.BlogPost")
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("blogs:blog_posts")

    def test_get_htmx(self):
        """verify call to GetBlogPost view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blogs/partials/list/blog_posts.htm")
        self.assertIn(self.instance.title, response.content.decode("utf-8"))

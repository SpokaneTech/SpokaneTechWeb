"""Development resources, real blog data, and About-page navigation."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker


class DevelopPageTests(TestCase):
    def setUp(self):
        self.url = reverse("web:develop")
        self.platform = baker.make("blogs.BlogPlatform", enabled=True, name="Community blog")
        self.tag = baker.make("blogs.BlogTag", value="Django")
        self.series = baker.make("blogs.BlogSeries", name="Building SpokaneTech")
        self.post = baker.make(
            "blogs.BlogPost",
            platform=self.platform,
            title="A community contribution",
            description="<p>Build &amp; learn.</p><p>Share ideas.</p>",
            url="https://example.com/community-contribution",
            author="Community author",
            series=self.series,
        )
        self.post.tags.add(self.tag)
        disabled = baker.make("blogs.BlogPlatform", enabled=False)
        self.hidden = baker.make("blogs.BlogPost", platform=disabled, title="Disabled platform post")

    def test_initial_and_htmx_render_real_posts_and_resources(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            with self.subTest(headers=headers):
                response = self.client.get(self.url, **headers)
                for value in (
                    self.post.title,
                    self.post.url,
                    self.tag.value,
                    self.series.name,
                    self.post.author,
                    "Build &amp; learn. Share ideas.",
                    "https://github.com/SpokaneTech/SpokaneTechWeb",
                ):
                    self.assertContains(response, value)
                self.assertContains(response, '<h1 id="develop-title">', count=1)
                self.assertNotContains(response, self.hidden.title)
                self.assertNotContains(response, 'hx-trigger="load"')
                self.assertNotContains(response, "const scrollContainer")
                self.assertNotContains(response, "&amp;amp;")
                if headers:
                    self.assertNotContains(response, "<html")
                else:
                    self.assertTemplateUsed(response, "base.htm")

    def test_about_has_a_contribution_link_in_its_content(self):
        response = self.client.get(reverse("web:about"))
        self.assertContains(response, f'class="st-text-link" href="{self.url}" hx-get="{self.url}"')

    def test_empty_posts_have_helpful_state(self):
        self.platform.enabled = False
        self.platform.save()
        response = self.client.get(self.url)
        self.assertContains(response, "Development updates will appear here as they're published.")
        self.assertNotContains(response, 'id="development-carousel"')

    @override_settings(DEBUG=False)
    def test_queries_are_constant_with_tags_and_series(self):
        with CaptureQueriesContext(connection) as small:
            self.client.get(self.url)
        latest = None
        for _ in range(8):
            latest = baker.make("blogs.BlogPost", platform=self.platform, series=self.series)
            latest.tags.add(self.tag)
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(self.url)
        self.assertEqual(response.context["blog_posts"][0].pk, latest.pk)
        self.assertEqual(len(response.context["blog_posts"]), 9)
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 2)

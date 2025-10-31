import os
import random
from pathlib import Path

import django
from django.apps import apps
from django.test import TestCase

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

django.setup()
from model_bakery import baker


class BlogPlatformTests(TestCase):
    """test CRUD operations on BlogPlatform"""

    def setUp(self):
        self.model = apps.get_model("blogs", "blogplatform")
        self.to_bake = "blogs.BlogPlatform"

    def bake(self):
        """add row"""
        return baker.make(
            self.to_bake,
        )

    def test_create(self):
        """verify object can be created"""
        before_count = self.model.objects.count()
        row = self.bake()
        after_count = self.model.objects.count()
        self.assertTrue(isinstance(row, self.model))
        self.assertGreater(after_count, before_count)

    def test_read(self):
        """verify object can be read"""
        row = self.bake()
        entry = self.model.objects.get(pk=row.pk)
        self.assertTrue(isinstance(entry, self.model))
        self.assertEqual(row.pk, entry.pk)

    def test_delete(self):
        """verify object can be deleted"""
        row = self.bake()
        before_count = self.model.objects.count()
        row_pk = row.pk
        row.delete()
        after_count = self.model.objects.count()
        with self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(pk=row_pk)
        self.assertLess(after_count, before_count)

    def test_update_name(self):
        """verify name (CharField) can be updated"""
        row = self.bake()
        original_value = row.name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["name"]).name
        setattr(row, "name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "name"), updated_value)
        self.assertNotEqual(getattr(row, "name"), original_value)

    def test_update_website_url(self):
        """verify website_url (CharField) can be updated"""
        row = self.bake()
        original_value = row.website_url
        updated_value = baker.prepare(self.to_bake, _fill_optional=["website_url"]).website_url
        setattr(row, "website_url", updated_value)
        row.save()
        self.assertEqual(getattr(row, "website_url"), updated_value)
        self.assertNotEqual(getattr(row, "website_url"), original_value)


class BlogPostTests(TestCase):
    """test CRUD operations on BlogPost"""

    def setUp(self):
        self.model = apps.get_model("blogs", "blogpost")
        self.to_bake = "blogs.BlogPost"

    def bake(self):
        """add row"""
        return baker.make(
            self.to_bake,
        )

    def test_create(self):
        """verify object can be created"""
        before_count = self.model.objects.count()
        row = self.bake()
        after_count = self.model.objects.count()
        self.assertTrue(isinstance(row, self.model))
        self.assertGreater(after_count, before_count)

    def test_read(self):
        """verify object can be read"""
        row = self.bake()
        entry = self.model.objects.get(pk=row.pk)
        self.assertTrue(isinstance(entry, self.model))
        self.assertEqual(row.pk, entry.pk)

    def test_delete(self):
        """verify object can be deleted"""
        row = self.bake()
        before_count = self.model.objects.count()
        row_pk = row.pk
        row.delete()
        after_count = self.model.objects.count()
        with self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(pk=row_pk)
        self.assertLess(after_count, before_count)

    def test_update_author(self):
        """verify author (CharField) can be updated"""
        row = self.bake()
        original_value = row.author
        updated_value = baker.prepare(self.to_bake, _fill_optional=["author"]).author
        setattr(row, "author", updated_value)
        row.save()
        self.assertEqual(getattr(row, "author"), updated_value)
        self.assertNotEqual(getattr(row, "author"), original_value)

    def test_update_description(self):
        """verify description (TextField) can be updated"""
        row = self.bake()
        original_value = row.description
        updated_value = baker.prepare(self.to_bake, _fill_optional=["description"]).description
        setattr(row, "description", updated_value)
        row.save()
        self.assertEqual(getattr(row, "description"), updated_value)
        self.assertNotEqual(getattr(row, "description"), original_value)

    def test_update_platform(self):
        """verify platform (ForeignKey) can be updated"""
        row = self.bake()
        original_value = row.platform
        baker.make(self.model.platform.field.related_model._meta.label, _fill_optional=True)
        if original_value:
            updated_value = random.choice(self.model.platform.field.related_model.objects.exclude(pk=original_value.pk))
        else:
            updated_value = random.choice(self.model.platform.field.related_model.objects.all())
        setattr(row, "platform", updated_value)
        row.save()
        self.assertEqual(getattr(row, "platform"), updated_value)
        self.assertNotEqual(getattr(row, "platform"), original_value)

    def test_update_series(self):
        """verify series (ForeignKey) can be updated"""
        row = self.bake()
        original_value = row.series
        baker.make(self.model.series.field.related_model._meta.label, _fill_optional=True)
        if original_value:
            updated_value = random.choice(self.model.series.field.related_model.objects.exclude(pk=original_value.pk))
        else:
            updated_value = random.choice(self.model.series.field.related_model.objects.all())
        setattr(row, "series", updated_value)
        row.save()
        self.assertEqual(getattr(row, "series"), updated_value)
        self.assertNotEqual(getattr(row, "series"), original_value)

    def test_update_title(self):
        """verify title (CharField) can be updated"""
        row = self.bake()
        original_value = row.title
        updated_value = baker.prepare(self.to_bake, _fill_optional=["title"]).title
        setattr(row, "title", updated_value)
        row.save()
        self.assertEqual(getattr(row, "title"), updated_value)
        self.assertNotEqual(getattr(row, "title"), original_value)

    def test_update_url(self):
        """verify url (CharField) can be updated"""
        row = self.bake()
        original_value = row.url
        updated_value = baker.prepare(self.to_bake, _fill_optional=["url"]).url
        setattr(row, "url", updated_value)
        row.save()
        self.assertEqual(getattr(row, "url"), updated_value)
        self.assertNotEqual(getattr(row, "url"), original_value)


class BlogSeriesTests(TestCase):
    """test CRUD operations on BlogSeries"""

    def setUp(self):
        self.model = apps.get_model("blogs", "blogseries")
        self.to_bake = "blogs.BlogSeries"

    def bake(self):
        """add row"""
        return baker.make(
            self.to_bake,
        )

    def test_create(self):
        """verify object can be created"""
        before_count = self.model.objects.count()
        row = self.bake()
        after_count = self.model.objects.count()
        self.assertTrue(isinstance(row, self.model))
        self.assertGreater(after_count, before_count)

    def test_read(self):
        """verify object can be read"""
        row = self.bake()
        entry = self.model.objects.get(pk=row.pk)
        self.assertTrue(isinstance(entry, self.model))
        self.assertEqual(row.pk, entry.pk)

    def test_delete(self):
        """verify object can be deleted"""
        row = self.bake()
        before_count = self.model.objects.count()
        row_pk = row.pk
        row.delete()
        after_count = self.model.objects.count()
        with self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(pk=row_pk)
        self.assertLess(after_count, before_count)

    def test_update_description(self):
        """verify description (TextField) can be updated"""
        row = self.bake()
        original_value = row.description
        updated_value = baker.prepare(self.to_bake, _fill_optional=["description"]).description
        setattr(row, "description", updated_value)
        row.save()
        self.assertEqual(getattr(row, "description"), updated_value)
        self.assertNotEqual(getattr(row, "description"), original_value)

    def test_update_name(self):
        """verify name (CharField) can be updated"""
        row = self.bake()
        original_value = row.name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["name"]).name
        setattr(row, "name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "name"), updated_value)
        self.assertNotEqual(getattr(row, "name"), original_value)

import os
import random
from pathlib import Path

import django
from django.apps import apps
from django.test import TestCase

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
from django.db.models.signals import post_save
from model_bakery import baker
from web.signals import event_post_to_linkedin_signal


class EventTests(TestCase):
    """test CRUD operations on Event"""

    def setUp(self):
        self.model = apps.get_model("web", "event")
        self.to_bake = "web.Event"
        post_save.disconnect(receiver=event_post_to_linkedin_signal, sender=self.to_bake)

    def tearDown(self):
        post_save.disconnect(receiver=event_post_to_linkedin_signal, sender=self.to_bake)

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

    def test_update_group(self):
        """verify group (ForeignKey) can be updated"""
        row = self.bake()
        original_value = row.group
        baker.make(self.model.group.field.related_model._meta.label, _fill_optional=["icon"])
        if original_value:
            updated_value = random.choice(self.model.group.field.related_model.objects.exclude(pk=original_value.pk))
        else:
            updated_value = random.choice(self.model.group.field.related_model.objects.all())
        setattr(row, "group", updated_value)
        row.save()
        self.assertEqual(getattr(row, "group"), updated_value)
        self.assertNotEqual(getattr(row, "group"), original_value)

    def test_update_location_address(self):
        """verify location_address (CharField) can be updated"""
        row = self.bake()
        original_value = row.location_address
        updated_value = baker.prepare(self.to_bake, _fill_optional=["location_address"]).location_address
        setattr(row, "location_address", updated_value)
        row.save()
        self.assertEqual(getattr(row, "location_address"), updated_value)
        self.assertNotEqual(getattr(row, "location_address"), original_value)

    def test_update_location_name(self):
        """verify location_name (CharField) can be updated"""
        row = self.bake()
        original_value = row.location_name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["location_name"]).location_name
        setattr(row, "location_name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "location_name"), updated_value)
        self.assertNotEqual(getattr(row, "location_name"), original_value)

    def test_update_map_link(self):
        """verify map_link (CharField) can be updated"""
        row = self.bake()
        original_value = row.map_link
        updated_value = baker.prepare(self.to_bake, _fill_optional=["map_link"]).map_link
        setattr(row, "map_link", updated_value)
        row.save()
        self.assertEqual(getattr(row, "map_link"), updated_value)
        self.assertNotEqual(getattr(row, "map_link"), original_value)

    def test_update_name(self):
        """verify name (CharField) can be updated"""
        row = self.bake()
        original_value = row.name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["name"]).name
        setattr(row, "name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "name"), updated_value)
        self.assertNotEqual(getattr(row, "name"), original_value)

    def test_update_social_platform_id(self):
        """verify social_platform_id (CharField) can be updated"""
        row = self.bake()
        original_value = row.social_platform_id
        updated_value = baker.prepare(self.to_bake, _fill_optional=["social_platform_id"]).social_platform_id
        setattr(row, "social_platform_id", updated_value)
        row.save()
        self.assertEqual(getattr(row, "social_platform_id"), updated_value)
        self.assertNotEqual(getattr(row, "social_platform_id"), original_value)

    def test_update_url(self):
        """verify url (CharField) can be updated"""
        row = self.bake()
        original_value = row.url
        updated_value = baker.prepare(self.to_bake, _fill_optional=["url"]).url
        setattr(row, "url", updated_value)
        row.save()
        self.assertEqual(getattr(row, "url"), updated_value)
        self.assertNotEqual(getattr(row, "url"), original_value)


class LinkTests(TestCase):
    """test CRUD operations on Link"""

    def setUp(self):
        self.model = apps.get_model("web", "link")
        self.to_bake = "web.Link"

    def bake(self):
        """add row"""
        return baker.make(self.to_bake, _fill_optional=["description", "name"])

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
        """verify description (CharField) can be updated"""
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

    def test_update_url(self):
        """verify url (CharField) can be updated"""
        row = self.bake()
        original_value = row.url
        updated_value = baker.prepare(self.to_bake, _fill_optional=["url"]).url
        setattr(row, "url", updated_value)
        row.save()
        self.assertEqual(getattr(row, "url"), updated_value)
        self.assertNotEqual(getattr(row, "url"), original_value)


class SocialPlatformTests(TestCase):
    """test CRUD operations on SocialPlatform"""

    def setUp(self):
        self.model = apps.get_model("web", "socialplatform")
        self.to_bake = "web.SocialPlatform"

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

    def test_update_base_url(self):
        """verify base_url (CharField) can be updated"""
        row = self.bake()
        original_value = row.base_url
        updated_value = baker.prepare(self.to_bake, _fill_optional=["base_url"]).base_url
        setattr(row, "base_url", updated_value)
        row.save()
        self.assertEqual(getattr(row, "base_url"), updated_value)
        self.assertNotEqual(getattr(row, "base_url"), original_value)

    def test_update_name(self):
        """verify name (CharField) can be updated"""
        row = self.bake()
        original_value = row.name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["name"]).name
        setattr(row, "name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "name"), updated_value)
        self.assertNotEqual(getattr(row, "name"), original_value)


class TagTests(TestCase):
    """test CRUD operations on Tag"""

    def setUp(self):
        self.model = apps.get_model("web", "tag")
        self.to_bake = "web.Tag"

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

    def test_update_value(self):
        """verify value (CharField) can be updated"""
        row = self.bake()
        original_value = row.value
        updated_value = baker.prepare(self.to_bake, _fill_optional=["value"]).value
        setattr(row, "value", updated_value)
        row.save()
        self.assertEqual(getattr(row, "value"), updated_value)
        self.assertNotEqual(getattr(row, "value"), original_value)


class TechGroupTests(TestCase):
    """test CRUD operations on TechGroup"""

    def setUp(self):
        self.model = apps.get_model("web", "techgroup")
        self.to_bake = "web.TechGroup"

    def bake(self):
        """add row"""
        return baker.make(self.to_bake, _fill_optional=["icon"])

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

    def test_update_icon(self):
        """verify icon (CharField) can be updated"""
        row = self.bake()
        original_value = row.icon
        updated_value = baker.prepare(self.to_bake, _fill_optional=["icon"]).icon
        setattr(row, "icon", updated_value)
        row.save()
        self.assertEqual(getattr(row, "icon"), updated_value)
        self.assertNotEqual(getattr(row, "icon"), original_value)

    def test_update_name(self):
        """verify name (CharField) can be updated"""
        row = self.bake()
        original_value = row.name
        updated_value = baker.prepare(self.to_bake, _fill_optional=["name"]).name
        setattr(row, "name", updated_value)
        row.save()
        self.assertEqual(getattr(row, "name"), updated_value)
        self.assertNotEqual(getattr(row, "name"), original_value)

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

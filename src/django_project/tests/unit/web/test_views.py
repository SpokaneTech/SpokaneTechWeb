import os
from pathlib import Path

import django
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
from model_bakery import baker


class TestAboutView(TestCase):
    def setUp(self):
        super(TestAboutView, self).setUp()
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:about")

    def test_get(self):
        """verify call to GetAboutContent view with a non-htmx call"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/custom/about.html")

    def test_get_htmx(self):
        """verify call to GetAboutContent view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/custom/about.htm")


class TestCalendarView(TestCase):
    def setUp(self):
        super(TestCalendarView, self).setUp()
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.now = timezone.now()
        self.url = reverse("web:event_calendar", kwargs={"year": self.now.year, "month": self.now.month})

    def test_get(self):
        """verify call to EventCalendarView view with a non-htmx call"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/custom/calendar.html")

    def test_get_htmx(self):
        """verify call to EventCalendarView view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/custom/calendar.htm")


class TestIndexView(TestCase):
    def setUp(self):
        super(TestIndexView, self).setUp()
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:index")

    def test_default(self):
        """verify call to GetIndexContent view via 'default' url with a non-htmx call"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/custom/index.html")

    def test_default_htmx(self):
        """verify call to GetIndexContent view via 'default' with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/custom/index.htm")


class TestGetTechEventView(TestCase):
    def setUp(self):
        super(TestGetTechEventView, self).setUp()
        self.instance = baker.make("web.Event")
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:get_event", kwargs={"pk": self.instance.pk})

    def test_get(self):
        """verify call to GetTechEvent view with a non-htmx call"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/detail/event.html")

    def test_get_htmx(self):
        """verify call to GetTechEvent view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/detail/event.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))


class TestGetTechEventsView(TestCase):
    def setUp(self):
        super(TestGetTechEventsView, self).setUp()
        self.instance = baker.make("web.Event")
        self.headers = dict(HTTP_HX_REQUEST="true")

    def test_get(self):
        """verify call to GetTechEvents view with a non-htmx call"""
        url = reverse("web:get_events")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/list/events.html")

    def test_get_htmx_index(self):
        """verify call to GetTechEvents view with a htmx call"""
        url = reverse("web:get_events", kwargs={"display": "marquee"})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/marquee/events.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))

    def test_get_htmx_list(self):
        """verify call to GetTechEvents view with a htmx call"""
        url = reverse("web:get_events", kwargs={"display": "list"})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/list/events.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))


class GetTechEventModalView(TestCase):
    def setUp(self):
        super(GetTechEventModalView, self).setUp()
        self.instance = baker.make("web.Event")
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:techevent_modal", kwargs={"pk": self.instance.pk})

    def test_get_htmx(self):
        """verify call to GetTechEventModal view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/modal/event_information.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))


class TestGetTechGroupView(TestCase):
    def setUp(self):
        super(TestGetTechGroupView, self).setUp()
        self.instance = baker.make("web.TechGroup")
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:get_techgroup", kwargs={"pk": self.instance.pk})

    def test_get(self):
        """verify call to GetTechGroup view with a non-htmx call"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/detail/group.html")

    def test_get_htmx(self):
        """verify call to GetTechGroup view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/detail/group.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))


class TestGetTechGroupsView(TestCase):
    def setUp(self):
        super(TestGetTechGroupsView, self).setUp()
        self.instance = baker.make("web.TechGroup")
        self.headers = dict(HTTP_HX_REQUEST="true")

    def test_get(self):
        """verify call to GetTechGroups view with a non-htmx call"""
        url = reverse("web:get_techgroups")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/full/list/groups.html")

    def test_get_htmx_index(self):
        """verify call to GetTechGroups view with a htmx call"""
        url = reverse("web:get_techgroups", kwargs={"display": "marquee"})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/marquee/groups.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))

    def test_get_htmx_list(self):
        """verify call to GetTechGroups view with a htmx call"""
        url = reverse("web:get_techgroups", kwargs={"display": "list"})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/list/groups.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))


class GetTechGroupModalView(TestCase):
    def setUp(self):
        super(GetTechGroupModalView, self).setUp()
        self.instance = baker.make("web.TechGroup")
        self.headers = dict(HTTP_HX_REQUEST="true")
        self.url = reverse("web:techgroup_modal", kwargs={"pk": self.instance.pk})

    def test_get_htmx(self):
        """verify call to GetTechGroupModal view with a htmx call"""
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/partials/modal/group_information.htm")
        self.assertIn(self.instance.name, response.content.decode("utf-8"))

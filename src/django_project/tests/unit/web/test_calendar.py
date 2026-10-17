"""Calendar rendering, Pacific month boundaries, and month navigation."""

import os
from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker


class CalendarTests(TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 6, tzinfo=datetime_timezone.utc)
        self.group = baker.make("web.TechGroup", name="Calendar builders")
        self.event = baker.make(
            "web.Event",
            group=self.group,
            name="October workshop",
            start_datetime=datetime(2026, 10, 20, 18, tzinfo=datetime_timezone.utc),
            location_name="Community space",
        )
        self.late = baker.make(
            "web.Event",
            group=self.group,
            name="Late October gathering",
            start_datetime=datetime(2026, 11, 1, 6, 30, tzinfo=datetime_timezone.utc),
        )
        self.next_month = baker.make(
            "web.Event",
            group=self.group,
            name="November gathering",
            start_datetime=datetime(2026, 11, 1, 7, tzinfo=datetime_timezone.utc),
        )
        self.previous_month = baker.make(
            "web.Event",
            name="September gathering",
            start_datetime=datetime(2026, 10, 1, 6, 59, tzinfo=datetime_timezone.utc),
        )
        self.url = reverse("web:event_calendar", kwargs={"year": 2026, "month": 10})

    def get_calendar(self, url=None, **headers):
        with patch("web.views.timezone.now", return_value=self.now):
            return self.client.get(url or self.url, **headers)

    def test_full_and_htmx_render_requested_month_and_actual_events(self):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}, {"HTTP_USER_AGENT": "Mobile browser"}):
            with self.subTest(headers=headers):
                response = self.get_calendar(**headers)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "October 2026")
                self.assertContains(response, self.event.name)
                self.assertContains(response, self.late.name)
                self.assertContains(response, self.group.name)
                self.assertContains(response, "11:00 AM")
                self.assertContains(response, "2 events")
                self.assertContains(response, self.event.get_absolute_url())
                self.assertContains(response, reverse("web:techevent_modal", kwargs={"pk": self.event.pk}))
                self.assertContains(response, "Community space")
                self.assertNotContains(response, self.next_month.name)
                self.assertNotContains(response, self.previous_month.name)
                self.assertNotContains(response, 'hx-trigger="load"')
                self.assertEqual(len(response.context["calendar_weeks"]), 5)
                if "HTTP_HX_REQUEST" in headers:
                    self.assertNotContains(response, "<html")
                else:
                    self.assertTemplateUsed(response, "base.htm")

    def test_pacific_days_and_today_include_month_and_year(self):
        response = self.get_calendar()
        days = [day for week in response.context["calendar_weeks"] for day in week if day["day"]]
        self.assertEqual([day["day"] for day in days if day["is_today"]], [31])
        self.assertEqual([event.pk for event in days[30]["events"]], [self.late.pk])
        self.assertContains(response, 'datetime="2026-10-31" aria-current="date"')
        response = self.get_calendar(reverse("web:event_calendar", kwargs={"year": 2025, "month": 10}))
        self.assertNotContains(response, 'aria-current="date"')

    def test_current_month_routes_use_pacific_date(self):
        for url in (reverse("web:event_calendar"), reverse("web:event_calendar", kwargs={"year": 0, "month": 0})):
            for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
                with self.subTest(url=url, headers=headers):
                    response = self.get_calendar(url, **headers)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual((response.context["year"], response.context["month"]), (2026, 10))
                    self.assertContains(response, self.late.name)
                    self.assertEqual(response.context["today_url"], self.url)

    def test_navigation_rolls_years_and_preserves_actual_links(self):
        response = self.get_calendar(reverse("web:event_calendar", kwargs={"year": 2026, "month": 12}))
        self.assertEqual(
            response.context["next_month_url"], reverse("web:event_calendar", kwargs={"year": 2027, "month": 1})
        )
        self.assertEqual(
            response.context["prev_month_url"], reverse("web:event_calendar", kwargs={"year": 2026, "month": 11})
        )
        self.assertEqual(response.context["today_url"], self.url)
        self.assertContains(response, 'hx-push-url="true"')

    def test_daylight_saving_repeated_hour_stays_on_correct_day(self):
        events = [
            baker.make("web.Event", start_datetime=datetime(2026, 11, 1, hour, 30, tzinfo=datetime_timezone.utc))
            for hour in (8, 9)
        ]
        response = self.get_calendar(reverse("web:event_calendar", kwargs={"year": 2026, "month": 11}))
        self.assertEqual(
            [event.pk for event in response.context["agenda_days"][0]["events"]],
            [self.next_month.pk, *[event.pk for event in events]],
        )
        self.assertContains(response, "1:30 AM PDT")
        self.assertContains(response, "1:30 AM PST")

    def test_empty_month_and_invalid_dates(self):
        response = self.get_calendar(reverse("web:event_calendar", kwargs={"year": 2027, "month": 2}))
        self.assertContains(response, "No events listed for February.")
        self.assertEqual(len(response.context["calendar_weeks"]), 4)
        self.assertContains(response, "0 events")
        for year, month in ((2026, 13), (9999, 1)):
            self.assertEqual(
                self.get_calendar(reverse("web:event_calendar", kwargs={"year": year, "month": month})).status_code, 400
            )

    @override_settings(DEBUG=False)
    def test_related_group_queries_are_bounded(self):
        with CaptureQueriesContext(connection) as small:
            self.get_calendar()
        for _ in range(8):
            group = baker.make("web.TechGroup")
            baker.make("web.Event", group=group, start_datetime=self.event.start_datetime)
        with CaptureQueriesContext(connection) as large:
            response = self.get_calendar()
        self.assertContains(response, "10 events")
        self.assertEqual(len(small), len(large))
        self.assertLessEqual(len(large), 1)

"""Produce human-reviewable event promotion data without posting or calling AI."""

import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from web.models import Event
from web.seo import campaign_url


class Command(BaseCommand):
    help = "Preview upcoming event links for organic promotion; never sends messages."

    def add_arguments(self, parser):
        parser.add_argument("--source", choices=["linkedin", "discord", "partner"], default="linkedin")

    def handle(self, *args, **options):
        now = timezone.now()
        events = (
            Event.objects.filter(
                status=Event.Status.ACTIVE,
                start_datetime__gte=now,
                start_datetime__lt=now + timedelta(days=7),
                group__enabled=True,
            )
            .exclude(url="")
            .select_related("group")
            .order_by("start_datetime", "pk")[:10]
        )
        preview = [
            {
                "name": event.name,
                "group": event.group.name,
                "start": timezone.localtime(event.start_datetime, ZoneInfo("America/Los_Angeles")).isoformat(),
                "discovery_url": campaign_url(event.get_absolute_url(), options["source"], "weekly_events"),
                "rsvp_url": event.url,
            }
            for event in events
        ]
        self.stdout.write(json.dumps(preview, indent=2, ensure_ascii=True))

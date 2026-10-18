"""Only preferred, indexable public pages are advertised to crawlers."""

from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from web.models import Event, TechGroup
from web.seo import public_origin


class PublicSitemap(Sitemap):
    protocol = "https"
    limit = 50000

    def get_urls(self, page=1, site=None, protocol=None):
        site = SimpleNamespace(domain=urlsplit(public_origin()).netloc)
        return super().get_urls(page=page, site=site, protocol="https")


class StaticSitemap(PublicSitemap):
    def items(self):
        return (
            ["index", "events", "groups", "about", "develop", "newcomer_guide", "community_guide"]
            if settings.SEO_INDEXING_ENABLED
            else []
        )

    def location(self, item):
        if item == "index":
            return "/"
        if item in {"events", "groups"}:
            return reverse("web:get_events" if item == "events" else "web:get_techgroups", kwargs={"display": "list"})
        return reverse("web:" + item)


class GroupSitemap(PublicSitemap):
    def items(self):
        return TechGroup.objects.filter(enabled=True).order_by("pk") if settings.SEO_INDEXING_ENABLED else []


class EventSitemap(PublicSitemap):
    def items(self):
        if not settings.SEO_INDEXING_ENABLED:
            return []
        return (
            Event.objects.filter(status=Event.Status.ACTIVE, start_datetime__gte=timezone.now())
            .filter(Q(group__enabled=True) | Q(group__isnull=True))
            .order_by("pk")
        )


sitemaps = {"static": StaticSitemap, "groups": GroupSitemap, "events": EventSitemap}

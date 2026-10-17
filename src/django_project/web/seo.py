"""Search metadata built from public routes and actual application content."""

import json
import re
from typing import Any
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from web.models import Event, TechGroup
from web.utilities.html_utils import convert_html_to_text

STATIC_PAGES = {
    "web:index": (
        "Spokane Tech Events, Meetups & Groups | SpokaneTech",
        "Discover upcoming tech events, developer meetups, and local communities in Spokane and the Inland Northwest.",
    ),
    "web:get_events": (
        "Upcoming Tech Events in Spokane | SpokaneTech",
        "Find upcoming Spokane tech meetups and workshops. Explore dates, locations, hosts, and direct RSVP links.",
    ),
    "web:get_techgroups": (
        "Spokane Tech Groups & Developer Communities | SpokaneTech",
        "Explore Spokane's technology communities, their topics, and their upcoming events. Find a local group to join.",
    ),
    "web:about": (
        "About SpokaneTech | Spokane's Tech Community",
        "Learn about SpokaneTech and our community directory of local technology groups and events.",
    ),
    "web:develop": (
        "Develop with SpokaneTech | Contribute to the Community",
        "Help build SpokaneTech.org. Explore the open-source project, fork the repository, and contribute code, design, or documentation.",
    ),
    "web:privacy": (
        "Privacy Policy | SpokaneTech",
        "How SpokaneTech.org uses cookies, analytics, and information from visitors and public event sources.",
    ),
    "web:terms": (
        "Terms of Service | SpokaneTech",
        "Terms for using SpokaneTech.org's public directory of technology groups and events.",
    ),
    "web:newcomer_guide": (
        "Your First Spokane Tech Meetup | SpokaneTech",
        "Find your first tech meetup in Spokane: explore real upcoming events, choose a group, and check the details before you go.",
    ),
    "web:community_guide": (
        "Find a Spokane Developer Community | SpokaneTech",
        "Explore local tech communities by their actual topics and upcoming events, with practical advice for choosing a group.",
    ),
}
CAMPAIGN_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def public_origin() -> str:
    """Use an operator-controlled HTTPS origin, never an incoming Host header."""
    value = settings.PUBLIC_SITE_URL.rstrip("/")
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or parts.path
    ):
        raise ImproperlyConfigured(
            "PUBLIC_SITE_URL must be an HTTPS origin without credentials, path, query or fragment"
        )
    return value


def absolute_url(path: str) -> str:
    if path.startswith("/") and not path.startswith("//"):
        return public_origin() + path
    parts = urlsplit(path)
    return path if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password else ""


def campaign_url(path: str, source: str, campaign: str = "event_discovery") -> str:
    """A first-party discovery link; provider RSVP URLs stay unchanged."""
    return (
        absolute_url(path)
        + "?"
        + urlencode({"utm_source": source, "utm_medium": "organic_social", "utm_campaign": campaign})
    )


def text_summary(value: str, limit: int = 160) -> str:
    text = " ".join(convert_html_to_text(value, block_separator=" ").split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def script_json(value: Any) -> str:
    """JSON for inert page state or JSON-LD, safe even with source HTML in text."""
    encoded = json.dumps(value, ensure_ascii=True).translate(
        {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}
    )
    return encoded


def event_is_public(event: Event) -> bool:
    return not event.group_id or event.group.enabled


def event_schema(event: Event, canonical: str) -> dict:
    """Only reviewed, public physical events with a real venue get Event markup."""
    if (
        not event.event_schema_verified
        or not event_is_public(event)
        or not event.location_name
        or not event.location_address
    ):
        return {}
    result = {
        "@context": "https://schema.org",
        "@type": "Event",
        "@id": canonical + "#event",
        "url": canonical,
        "name": event.name,
        "startDate": timezone.localtime(event.start_datetime, ZoneInfo("America/Los_Angeles")).isoformat(),
        "eventStatus": "https://schema.org/EventCancelled"
        if event.is_cancelled
        else "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "name": event.location_name,
            "address": {"@type": "PostalAddress", "name": event.location_address},
        },
    }
    if event.description:
        result["description"] = text_summary(event.description, 1000)
    if event.end_datetime and event.end_datetime >= event.start_datetime:
        result["endDate"] = timezone.localtime(event.end_datetime, ZoneInfo("America/Los_Angeles")).isoformat()
    if event.image:
        image = absolute_url(event.image.url)
        if image:
            result["image"] = [image]
    if event.group_id:
        result["organizer"] = {
            "@type": "Organization",
            "name": event.group.name,
            "url": absolute_url(event.group.get_absolute_url()),
        }
    return result


def page_metadata(request) -> dict:
    """Route policy is shared by HTML, response headers, history and analytics."""
    cached = getattr(request, "page_seo", None)
    if cached is not None:
        return cached
    match = request.resolver_match
    route = match.view_name if match else ""
    kwargs = match.kwargs if match else {}
    obj = getattr(request, "seo_object", None)
    title, description = STATIC_PAGES.get(route, ("SpokaneTech", "Spokane's technology groups and events."))
    path = request.path
    public = route in STATIC_PAGES
    indexable = public
    image = absolute_url(static("spokanetech/img/spokane-community-illustration.jpg"))
    image_alt = "SpokaneTech community"
    schema: list[dict[str, Any]] = []
    parent = None
    if route == "web:index":
        path = "/"
        schema = [
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "@id": public_origin() + "/#organization",
                "name": "SpokaneTech",
                "url": public_origin() + "/",
            },
            {"@context": "https://schema.org", "@type": "WebSite", "name": "SpokaneTech", "url": public_origin() + "/"},
        ]
        profiles = [
            url
            for url in getattr(settings, "SEO_VERIFIED_PROFILE_URLS", [])
            if url.startswith("https://") and absolute_url(url)
        ]
        if profiles:
            schema[0]["sameAs"] = profiles
    elif route in {"web:get_events", "web:get_techgroups"}:
        path = reverse(route, kwargs={"display": "list"})
        indexable = kwargs.get("display") in (None, "list") and not any(key not in CAMPAIGN_KEYS for key in request.GET)
    elif route == "web:get_event" and isinstance(obj, Event):
        public = event_is_public(obj)
        indexable = public
        local_date = timezone.localtime(obj.start_datetime, ZoneInfo("America/Los_Angeles")).strftime("%b %d, %Y")
        title = f"{'Cancelled: ' if obj.is_cancelled else ''}{obj.name} — {local_date} | SpokaneTech"
        description = (
            text_summary(obj.description)
            or f"Details, date, and location for {obj.name}. Check the organizer's event page before attending."
        )
        parent = ("Events", reverse("web:get_events", kwargs={"display": "list"}))
        if obj.image:
            image = absolute_url(obj.image.url) or image
            image_alt = obj.name
        data = event_schema(obj, absolute_url(path)) if public else {}
        if data:
            schema = [data]
    elif route == "web:get_techgroup" and isinstance(obj, TechGroup):
        public = obj.enabled
        indexable = public
        title = f"{obj.name} — Spokane Tech Community | SpokaneTech"
        description = (
            text_summary(obj.description)
            or f"Explore {obj.name} and its upcoming events in the Spokane tech community."
        )
        parent = ("Groups", reverse("web:get_techgroups", kwargs={"display": "list"}))
        if obj.image:
            image = absolute_url(obj.image.url) or image
            image_alt = obj.name
    elif route == "web:event_calendar":
        public = True
        indexable = False
        title, description = (
            "Spokane Tech Event Calendar | SpokaneTech",
            "Explore the community calendar of technology events in Spokane and the Inland Northwest.",
        )
        if kwargs.get("year", 0) == 0 and kwargs.get("month", 0) == 0:
            path = reverse("web:event_calendar")
    if parent and obj is not None:
        schema.append(
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": absolute_url("/")},
                    {"@type": "ListItem", "position": 2, "name": parent[0], "item": absolute_url(parent[1])},
                    {"@type": "ListItem", "position": 3, "name": obj.name, "item": absolute_url(path)},
                ],
            }
        )
    canonical = absolute_url(path)
    campaign = {
        key: request.GET[key]
        for key in CAMPAIGN_KEYS
        if key in request.GET and re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", request.GET[key])
    }
    metadata = {
        "analytics_location": canonical + ("?" + urlencode(sorted(campaign.items())) if campaign else ""),
        "title": title,
        "description": description,
        "canonical": canonical,
        "image": image,
        "image_alt": image_alt,
        "robots": "index, follow" if indexable and settings.SEO_INDEXING_ENABLED else "noindex, follow",
        "public": public,
        "indexable": indexable,
        "structured_data": schema if public else [],
        "manual_page_views": settings.GA4_MANUAL_PAGE_VIEWS,
    }
    request.page_seo = metadata
    return metadata


def promotion_link(event: Event, source: str, campaign: str = "event_discovery") -> str:
    """Opt-in to first-party discovery only after a channel is approved."""
    if getattr(settings, "PROMOTE_SITE_LINKS", False) is True and event_is_public(event):
        return campaign_url(event.get_absolute_url(), source, campaign)
    return event.url

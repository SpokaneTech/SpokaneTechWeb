import sys

import django
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_GET
from web.models import Event, TechGroup


@require_GET
def robots_txt(request) -> HttpResponse:
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = [
        "User-Agent: *",
        "Disallow: /__debug__/",
        "Disallow: /accounts/",
        "Disallow: /admin/",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


@require_GET
def sitemap_xml(request) -> HttpResponse:
    static_urls: list[str] = [
        request.build_absolute_uri(reverse("web:index")),
        request.build_absolute_uri(reverse("web:about")),
        request.build_absolute_uri(reverse("web:develop")),
        request.build_absolute_uri(reverse("web:get_events")),
        request.build_absolute_uri(reverse("web:get_techgroups")),
        request.build_absolute_uri(reverse("web:event_calendar")),
    ]
    event_urls = [request.build_absolute_uri(event.get_absolute_url()) for event in Event.objects.all()]
    tech_group_urls = [request.build_absolute_uri(group.get_absolute_url()) for group in TechGroup.objects.all()]

    url_entries = "".join(f"<url><loc>{url}</loc></url>" for url in static_urls + event_urls + tech_group_urls)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{url_entries}"
        "</urlset>"
    )
    return HttpResponse(content, content_type="application/xml")


class HostView(View):
    def get(self, request) -> HttpResponse:
        host_info: dict[str, str] = {
            "hostname": request.get_host(),
            "remote_ip_address": request.META.get("REMOTE_ADDR", "Unknown"),
            "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
            "source_code": getattr(settings, "PROJECT_SOURCE", "Unknown"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "django_version": django.get_version(),
        }
        return render(request, "core/host_info.html", host_info)

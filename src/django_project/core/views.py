import sys

import django
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request) -> HttpResponse:
    from web.seo import absolute_url

    if not settings.SEO_INDEXING_ENABLED:
        content = "User-Agent: *\nDisallow: /\n"
    else:
        content = (
            "User-Agent: *\nDisallow: /__debug__/\nDisallow: /accounts/\n"
            "Disallow: /console/\nDisallow: /admin/\n"
            f"Sitemap: {absolute_url('/sitemap.xml')}\n"
        )
    return HttpResponse(content, content_type="text/plain")


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

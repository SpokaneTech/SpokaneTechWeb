"""Search response policy for full HTML, HTMX and utility endpoints."""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from web.seo import page_metadata, script_json


def seo_context(request):
    metadata = page_metadata(request)
    return {
        "SEO_INDEXING_ENABLED": settings.SEO_INDEXING_ENABLED,
        "GA4_MANUAL_PAGE_VIEWS": settings.GA4_MANUAL_PAGE_VIEWS,
        "seo": metadata,
        "seo_page_json": script_json(metadata),
        "seo_schema_json": script_json(metadata["structured_data"]),
    }


class SEOMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # HTMX history misses must receive full HTML for proper document restoration.
        if request.headers.get("HX-History-Restore-Request") == "true":
            request.META.pop("HTTP_HX_REQUEST", None)
            request.__dict__.pop("headers", None)
        if request.path == "/index/" and request.method in ("GET", "HEAD") and not request.headers.get("HX-Request"):
            query = request.META.get("QUERY_STRING", "")
            response = HttpResponsePermanentRedirect("/" + ("?" + query if query else ""))
        else:
            response = self.get_response(request)
        patch_vary_headers(response, ("HX-Request", "HX-History-Restore-Request"))
        metadata = page_metadata(request)
        html = response.get("Content-Type", "").startswith("text/html")
        partial = bool(request.headers.get("HX-Request"))
        if response.status_code >= 400 or metadata["robots"].startswith("noindex") or partial:
            response["X-Robots-Tag"] = "noindex, follow"
        # A small inert payload is saved inside body_main by HTMX, including history snapshots.
        is_page = metadata["public"] or getattr(request, "seo_object", None) is not None
        if html and response.status_code == 200 and partial and is_page:
            payload = render_to_string("core/partials/page_metadata.htm", {"seo_page_json": script_json(metadata)})
            response.content = payload.encode(response.charset) + response.content
            response["Content-Length"] = len(response.content)
        return response

import json

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.html import strip_tags
from handyhelpers.views.calendar import HtmxCalendarView
from handyhelpers.views.htmx import (
    HtmxOptionDetailView,
    HtmxOptionMultiFilterView,
    HtmxOptionView,
    ModelDetailBootstrapModalView,
)
from web.models import Event, TechGroup


class SeoContextMixin:
    """
    Mixin class that provides SEO context and metadata to Django class-based views.
    This mixin automatically populates the template context with SEO-related metadata
    including meta titles, descriptions, keywords, canonical URLs, Open Graph tags,
    and structured data markup. Subclasses can override the getter methods to customize
    metadata for specific views.
    Attributes:
        default_meta_description (str): Default meta description used if not overridden.
        default_meta_keywords (str): Default meta keywords used if not overridden.
        meta_title (str): Meta title for the page.
        og_type (str): Open Graph type (e.g., 'website', 'article').
    Methods:
        get_meta_title(): Returns the meta title for the page.
        get_meta_description(): Returns the meta description for the page.
        get_meta_keywords(): Returns comma-separated keywords for the page.
        get_canonical_url(): Returns the canonical URL for the current request.
        get_structured_data(): Returns structured data markup (JSON-LD) or None if not applicable.
        get_context_data(**kwargs): Populates template context with all SEO metadata.
    Example:
        >>> class MyPageView(SeoContextMixin, TemplateView):
        ...     template_name = 'my_page.html'
        ...     meta_title = 'My Custom Page'
        ...
        ...     def get_meta_description(self):
        ...         return 'A custom description for my page'
    """

    default_meta_description: str = "Home of the Spokane and Inland Northwest tech community"
    default_meta_keywords: str = "spokane, spokanetech, tech, technology"
    meta_title: str = "Spokane Tech"
    og_type: str = "website"
    request: HttpRequest

    def get_meta_title(self) -> str:
        return self.meta_title

    def get_meta_description(self) -> str:
        return self.default_meta_description

    def get_meta_keywords(self) -> str:
        return self.default_meta_keywords

    def get_canonical_url(self) -> str:
        return self.request.build_absolute_uri()

    def get_structured_data(self) -> str | None:
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meta_title"] = self.get_meta_title()
        context["meta_description"] = self.get_meta_description()
        context["meta_keywords"] = self.get_meta_keywords()
        context["canonical_url"] = self.get_canonical_url()
        context["og_title"] = context["meta_title"]
        context["og_description"] = context["meta_description"]
        context["og_type"] = self.og_type
        context["structured_data"] = self.get_structured_data()
        return context


def linkedin_oauth_callback(request: HttpRequest) -> HttpResponse:
    """Display LinkedIn OAuth callback parameters for manual token exchange flows."""
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")
    error_description = request.GET.get("error_description")

    if error:
        body = ["LinkedIn OAuth callback received an error.", "", f"error: {error}"]
        if error_description:
            body.append(f"error_description: {error_description}")
        return HttpResponse("\n".join(body), content_type="text/plain", status=400)

    if not code:
        return HttpResponse(
            "LinkedIn OAuth callback did not include a code parameter.",
            content_type="text/plain",
            status=400,
        )

    body = [
        "LinkedIn OAuth callback received successfully.",
        "",
        f"code: {code}",
    ]
    if state:
        body.append(f"state: {state}")
    body.extend(
        [
            "",
            "Use this code with:",
            "python manage.py linkedin_oauth --redirect-uri <this exact callback URL> --code '<code>'",
        ]
    )
    return HttpResponse("\n".join(body), content_type="text/plain")


class AboutContentView(SeoContextMixin, HtmxOptionView):
    """Render the 'about' page"""

    htmx_template_name: str = "web/partials/custom/about.htm"
    template_name: str = "web/full/custom/about.html"
    meta_title = "About Spokane Tech | Inland Northwest Tech Community"
    default_meta_description = (
        "Learn about Spokane Tech, a community hub for Inland Northwest tech events, meetups, workshops, and"
        " collaboration."
    )


class DevelopContentView(SeoContextMixin, HtmxOptionView):
    """Render the 'development' page"""

    htmx_template_name: str = "web/partials/custom/develop.htm"
    template_name: str = "web/full/custom/develop.html"
    meta_title = "Develop With Spokane Tech | Open Source Community Project"
    default_meta_description = (
        "Contribute to Spokane Tech, follow project development, and explore community-written articles about"
        " building the site."
    )


class EventCalendarView(SeoContextMixin, HtmxCalendarView):
    """Render a monthly calendar view of Event instances"""

    event_detail_url: str = "web:techevent_modal"
    event_model = Event
    event_model_date_field: str = "start_datetime"
    htmx_template_name: str = "web/partials/custom/calendar.htm"
    template_name: str = "web/full/custom/calendar.html"
    title: str = "Spokane Tech Event Calendar"
    meta_title = "Spokane Tech Event Calendar | Spokane Tech"
    default_meta_description = (
        "Browse the Spokane Tech calendar for upcoming meetups, workshops, talks, and networking events."
    )

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "Mobile" in user_agent:
            self.htmx_template_name = "web/partials/custom/calendar_mobile.htm"
        return super().get(request, *args, **kwargs)


class IndexContentView(SeoContextMixin, HtmxOptionView):
    """Render the index page"""

    htmx_template_name: str = "web/partials/custom/index.htm"
    template_name: str = "web/full/custom/index.html"
    meta_title = "Spokane Tech | Spokane Events, Meetups, and Tech Groups"
    default_meta_description = (
        "Discover Spokane tech events, local meetups, community groups, and ways to connect with the Inland"
        " Northwest technology community."
    )


class TechEventView(SeoContextMixin, HtmxOptionDetailView):
    """Render detail page for an Event instance"""

    model = Event
    htmx_template_name: str = "web/partials/detail/event.htm"
    template_name: str = "web/full/detail/event.html"
    og_type = "article"

    def get_meta_title(self) -> str:
        return f"{self.object.name} | Spokane Tech Event"

    def get_meta_description(self) -> str:
        text = strip_tags(self.object.description or "").strip()
        if text:
            return text[:155]
        if self.object.group:
            return f"View details for {self.object.name}, hosted by {self.object.group.name}."
        return f"View details for {self.object.name} on Spokane Tech."

    def get_meta_keywords(self) -> str:
        keywords = ["spokane", "tech event", self.object.name]
        if self.object.group:
            keywords.append(self.object.group.name)
        keywords.extend(tag.value for tag in self.object.tags.all())
        return ", ".join(dict.fromkeys(keywords))

    def get_structured_data(self) -> str | None:
        event_data: dict[str, object] = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": self.object.name,
            "description": strip_tags(self.object.description or "").strip() or self.get_meta_description(),
            "startDate": self.object.start_datetime.isoformat(),
            "url": self.request.build_absolute_uri(self.object.get_absolute_url()),
        }
        if self.object.end_datetime:
            event_data["endDate"] = self.object.end_datetime.isoformat()
        if self.object.location_name or self.object.location_address:
            event_data["location"] = {
                "@type": "Place",
                "name": self.object.location_name or self.object.location_address,
                "address": self.object.location_address or "",
            }
        if self.object.group:
            event_data["organizer"] = {
                "@type": "Organization",
                "name": self.object.group.name,
                "url": self.request.build_absolute_uri(self.object.group.get_absolute_url()),
            }
        if self.object.url:
            event_data["offers"] = {
                "@type": "Offer",
                "url": self.object.url,
                "availability": "https://schema.org/InStock",
            }
        if self.object.tags.exists():
            event_data["keywords"] = ", ".join(tag.value for tag in self.object.tags.all())
        return json.dumps(event_data)


class TechEventsView(SeoContextMixin, HtmxOptionMultiFilterView):
    """Render a list of Event instances"""

    htmx_minimal_wrapper_template_name: str = "web/partials/li/events.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/events.htm"
    htmx_template_name: str = "web/partials/li/events.htm"
    template_name: str = "web/full/list/events.html"
    meta_title = "Upcoming Spokane Tech Events | Spokane Tech"
    default_meta_description = (
        "Browse upcoming Spokane-area tech events, including meetups, talks, workshops, and networking sessions."
    )
    default_meta_keywords = "spokane events, tech meetup, workshops, networking, inland northwest"

    def get(self, request, *args, **kwargs):
        self.queryset = Event.objects.filter(start_datetime__gte=timezone.now())
        return super().get(request, *args, **kwargs)


class TechEventModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying details of an Event instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/event_information.htm"
    modal_title: str = "Event Info"
    model = Event

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "Mobile" in user_agent:
            self.modal_template = "web/partials/modal/event_information_modal.htm"
        return super().get(request, *args, **kwargs)


class TechGroupView(SeoContextMixin, HtmxOptionDetailView):
    """Render detail page for a TechGroup instance"""

    model = TechGroup
    htmx_template_name: str = "web/partials/detail/group.htm"
    template_name: str = "web/full/detail/group.html"
    og_type = "article"

    def get_meta_title(self) -> str:
        return f"{self.object.name} | Spokane Tech Group"

    def get_meta_description(self) -> str:
        text = strip_tags(self.object.description or "").strip()
        if text:
            return text[:155]
        return f"Explore {self.object.name}, a Spokane Tech community group in the Inland Northwest."

    def get_meta_keywords(self) -> str:
        keywords = ["spokane", "tech group", self.object.name, self.object.platform.name]
        keywords.extend(tag.value for tag in self.object.tags.all())
        return ", ".join(dict.fromkeys(keywords))

    def get_structured_data(self) -> str | None:
        group_data: dict[str, object] = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.object.name,
            "description": strip_tags(self.object.description or "").strip() or self.get_meta_description(),
            "url": self.request.build_absolute_uri(self.object.get_absolute_url()),
        }
        same_as = [link.url for link in self.object.links.all()]
        if same_as:
            group_data["sameAs"] = same_as
        return json.dumps(group_data)


class TechGroupsView(SeoContextMixin, HtmxOptionMultiFilterView):
    """Render a list of TechGroup instances"""

    htmx_list_template_name: str = "web/partials/list/groups.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/wrapper_list.htm"
    htmx_template_name: str = "web/partials/marquee/groups.htm"
    queryset = TechGroup.objects.filter(enabled=True)
    template_name: str = "web/full/list/groups.html"
    meta_title = "Spokane Tech Groups | Inland Northwest Meetups and Communities"
    default_meta_description = (
        "Explore Spokane-area tech groups, communities, and meetup organizers across the Inland Northwest."
    )
    default_meta_keywords = "spokane tech groups, meetups, community, inland northwest, technology"


class TechGroupModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying get details of a TechGroup instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/group_information.htm"
    modal_title: str = "Group Info"
    model = TechGroup

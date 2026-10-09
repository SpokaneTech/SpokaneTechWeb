from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from handyhelpers.views.calendar import HtmxCalendarView
from handyhelpers.views.htmx import (
    HtmxOptionDetailView,
    HtmxOptionMultiFilterView,
    HtmxOptionView,
    ModelDetailBootstrapModalView,
)

from web.models import Event, Tag, TechGroup
from web.utilities.html_utils import convert_html_to_text
from web.utilities.icons import get_icon_classes


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


class AboutContentView(HtmxOptionView):
    """Render the 'about' page"""

    htmx_template_name: str = "web/partials/custom/about.htm"
    template_name: str = "web/full/custom/about.html"


class DevelopContentView(HtmxOptionView):
    """Render the 'development' page"""

    htmx_template_name: str = "web/partials/custom/develop.htm"
    template_name: str = "web/full/custom/develop.html"


class EventCalendarView(HtmxCalendarView):
    """Render a monthly calendar view of Event instances"""

    event_detail_url: str = "web:techevent_modal"
    event_model = Event
    event_model_date_field: str = "start_datetime"
    htmx_template_name: str = "web/partials/custom/calendar.htm"
    template_name: str = "web/full/custom/calendar.html"
    title: str = "Spokane Tech Event Calendar"

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "Mobile" in user_agent:
            self.htmx_template_name = "web/partials/custom/calendar_mobile.htm"
        return super().get(request, *args, **kwargs)


class IndexContentView(HtmxOptionView):
    """Render the index page"""

    htmx_template_name: str = "web/partials/custom/index.htm"
    template_name: str = "web/full/custom/index.html"

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        upcoming = Event.objects.filter(start_datetime__gte=now)
        groups = TechGroup.objects.filter(enabled=True)
        self.context = {
            "upcoming_events": list(
                upcoming.select_related("group").prefetch_related("tags").order_by("start_datetime", "pk")[:4]
            ),
            "homepage_groups": list(
                groups.annotate(upcoming_event_count=Count("event", filter=Q(event__start_datetime__gte=now)))
                .prefetch_related("tags")
                .order_by("name", "pk")
            ),
            "upcoming_event_count": upcoming.count(),
            "active_group_count": groups.count(),
            "community_tags": list(
                Tag.objects.filter(Q(techgroup__enabled=True) | Q(event__start_datetime__gte=now))
                .distinct()
                .order_by("value")[:12]
            ),
        }
        for group in self.context["homepage_groups"]:
            group.homepage_icon = get_icon_classes(group.icon)
        return super().get(request, *args, **kwargs)


class TechEventView(HtmxOptionDetailView):
    """Render detail page for an Event instance"""

    model = Event
    htmx_template_name: str = "web/partials/detail/event.htm"
    template_name: str = "web/full/detail/event.html"


class TechEventsView(HtmxOptionMultiFilterView):
    """Render a list of Event instances"""

    htmx_minimal_wrapper_template_name: str = "web/partials/li/events.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/events.htm"
    htmx_list_template_name: str = "web/partials/list/events.htm"
    htmx_template_name: str = "web/partials/li/events.htm"
    template_name: str = "web/full/list/events.html"

    def get(self, request, *args, **kwargs):
        self.queryset = Event.objects.filter(start_datetime__gte=timezone.now())
        if kwargs.get("display") == "li" or (not kwargs.get("display") and request.GET.get("display") == "li"):
            kwargs["display"] = "minimal"
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


class TechGroupView(HtmxOptionDetailView):
    """Render detail page for a TechGroup instance"""

    model = TechGroup
    htmx_template_name: str = "web/partials/detail/group.htm"
    template_name: str = "web/full/detail/group.html"


class TechGroupsView(HtmxOptionMultiFilterView):
    """Render a list of TechGroup instances"""

    htmx_list_template_name: str = "web/partials/list/groups.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/wrapper_list.htm"
    htmx_template_name: str = "web/partials/marquee/groups.htm"
    htmx_minimal_template_name: str = "web/partials/marquee/groups.htm"
    htmx_minimal_wrapper_template_name: str = "web/partials/marquee/groups.htm"
    queryset = TechGroup.objects.filter(enabled=True)
    default_display = "list"
    template_name: str = "web/full/list/groups.html"

    def get(self, request, *args, **kwargs):
        self.queryset = (
            TechGroup.objects.filter(enabled=True)
            .annotate(
                upcoming_event_count=Count("event", filter=Q(event__start_datetime__gte=timezone.now()), distinct=True)
            )
            .prefetch_related("tags")
            .order_by("name", "pk")
        )
        if kwargs.get("display") == "marquee" or (
            not kwargs.get("display") and request.GET.get("display") == "marquee"
        ):
            kwargs["display"] = "minimal"
        return super().get(request, *args, **kwargs)

    def filter_by_query_params(self, parameters=None):
        """Normalize icons on the same cached results used by the directory and HTMX partials."""
        queryset = super().filter_by_query_params(parameters)
        for group in queryset:
            group.homepage_icon = get_icon_classes(group.icon)
            group.directory_description = convert_html_to_text(group.description, block_separator=" ")
        return queryset


class TechGroupModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying get details of a TechGroup instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/group_information.htm"
    modal_title: str = "Group Info"
    model = TechGroup

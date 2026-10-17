import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from blogs.models import BlogPost
from django.core.exceptions import FieldError
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse
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


class PrivacyContentView(HtmxOptionView):
    """Render the public privacy policy."""

    htmx_template_name: str = "web/partials/custom/privacy.htm"
    template_name: str = "web/full/custom/privacy.html"


class TermsContentView(HtmxOptionView):
    """Render the public terms of service."""

    htmx_template_name: str = "web/partials/custom/terms.htm"
    template_name: str = "web/full/custom/terms.html"


class DevelopContentView(HtmxOptionView):
    """Render the 'development' page"""

    htmx_template_name: str = "web/partials/custom/develop.htm"
    template_name: str = "web/full/custom/develop.html"

    def get(self, request, *args, **kwargs):
        posts = list(
            BlogPost.objects.filter(platform__enabled=True)
            .select_related("platform", "series")
            .prefetch_related("tags")
            .order_by("-created_at", "-pk")
        )
        for post in posts:
            post.summary = convert_html_to_text(post.description, block_separator=" ")
        self.context = {"blog_posts": posts}
        return super().get(request, *args, **kwargs)


class EventCalendarView(HtmxCalendarView):
    """Render a monthly calendar view of Event instances"""

    event_detail_url: str = "web:techevent_modal"
    event_model = Event
    event_model_date_field: str = "start_datetime"
    htmx_template_name: str = "web/partials/custom/calendar.htm"
    template_name: str = "web/full/custom/calendar.html"
    title: str = "Community calendar"

    @staticmethod
    def calendar_url(year: int, month: int) -> str:
        """Build navigation links independently of the helper's URL utilities."""
        return reverse("web:event_calendar", kwargs={"year": year, "month": month})

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        pacific = ZoneInfo("America/Los_Angeles")
        today = timezone.localtime(timezone.now(), pacific).date()
        try:
            year = int(kwargs.get("year", request.GET.get("year", today.year))) or today.year
            month = int(kwargs.get("month", request.GET.get("month", today.month))) or today.month
            if not 1 <= year <= 9998 or not 1 <= month <= 12:
                raise ValueError
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid calendar date")

        next_year, next_month = self.get_next(year, month)
        start = datetime(year, month, 1, tzinfo=pacific)
        end = datetime(next_year, next_month, 1, tzinfo=pacific)
        events = list(
            Event.objects.filter(status=Event.Status.ACTIVE, start_datetime__gte=start, start_datetime__lt=end)
            .select_related("group")
            .order_by("start_datetime", "pk")
        )
        events_by_day: dict[int, list[Event]] = {}
        for event in events:
            local_start = timezone.localtime(event.start_datetime, pacific)
            # Django's date:"T" is blank for the repeated hour at the DST transition.
            event.calendar_timezone = local_start.tzname()
            events_by_day.setdefault(local_start.day, []).append(event)

        weeks = []
        agenda_days = []
        for week in calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(year, month):
            days = []
            for day in week:
                day_date = date(year, month, day) if day else None
                entry = {
                    "day": day,
                    "date": day_date,
                    "is_today": day_date == today,
                    "events": events_by_day.get(day, []),
                }
                days.append(entry)
                if entry["events"]:
                    agenda_days.append(entry)
            weeks.append(days)

        context = {
            "title": self.title,
            "month_name": calendar.month_name[month],
            "year": year,
            "month": month,
            "today": today,
            "calendar_weeks": weeks,
            "agenda_days": agenda_days,
            "event_list": events,
            "today_url": self.calendar_url(today.year, today.month),
            "prev_month_url": self.calendar_url(*self.get_previous(year, month)) if (year, month) != (1, 1) else None,
            "next_month_url": self.calendar_url(next_year, next_month) if (year, month) != (9998, 12) else None,
        }
        template = self.htmx_template_name if self.is_htmx() else self.template_name
        return render(request, template, context)


class IndexContentView(HtmxOptionView):
    """Render the index page"""

    htmx_template_name: str = "web/partials/custom/index.htm"
    template_name: str = "web/full/custom/index.html"

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        upcoming = Event.objects.filter(status=Event.Status.ACTIVE, start_datetime__gte=now)
        groups = TechGroup.objects.filter(enabled=True)
        self.context = {
            "upcoming_events": list(
                upcoming.filter(start_datetime__lt=now + timedelta(days=30))
                .select_related("group")
                .prefetch_related("tags")
                .order_by("start_datetime", "pk")
            ),
            "homepage_groups": list(
                groups.annotate(
                    upcoming_event_count=Count(
                        "event", filter=Q(event__start_datetime__gte=now, event__status=Event.Status.ACTIVE)
                    )
                )
                .prefetch_related("tags")
                .order_by("-upcoming_event_count", "name", "pk")
            ),
            "upcoming_event_count": upcoming.count(),
            "active_group_count": groups.count(),
            "community_tags": list(
                Tag.objects.filter(
                    Q(techgroup__enabled=True) | Q(event__start_datetime__gte=now, event__status=Event.Status.ACTIVE)
                )
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.seo_object = self.object
        context["event_has_ended"] = self.object.start_datetime < timezone.now()
        return context

    def get_queryset(self):
        return super().get_queryset().select_related("group").prefetch_related("tags")


class TechEventsView(HtmxOptionMultiFilterView):
    """Render a list of Event instances"""

    htmx_minimal_wrapper_template_name: str = "web/partials/li/events.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/events.htm"
    htmx_list_template_name: str = "web/partials/list/events.htm"
    htmx_template_name: str = "web/partials/li/events.htm"
    template_name: str = "web/full/list/events.html"
    default_display = "list"

    def filter_by_query_params(self):
        """Keep the public group_id filter supported across helper versions."""
        queryset = super().filter_by_query_params()
        if "group_id" in self.request.GET:
            value = self.request.GET["group_id"]
            group_id = None if value == "None" else value
            try:
                queryset = queryset.filter(group_id=group_id)
            except (TypeError, ValueError):
                return queryset.none()
        return queryset

    def get(self, request, *args, **kwargs):
        self.queryset = (
            Event.objects.filter(status=Event.Status.ACTIVE, start_datetime__gte=timezone.now())
            .select_related("group")
            .prefetch_related("tags")
            .order_by("start_datetime", "pk")
        )
        if kwargs.get("display") == "li" or (not kwargs.get("display") and request.GET.get("display") == "li"):
            kwargs["display"] = "minimal"
        return super().get(request, *args, **kwargs)


class TechEventModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying details of an Event instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/event_information.htm"
    modal_title: str = "Event details"
    template_name: str = "core/partials/modal_swap.htm"
    model = Event


class TechGroupView(HtmxOptionDetailView):
    """Render detail page for a TechGroup instance"""

    model = TechGroup
    htmx_template_name: str = "web/partials/detail/group.htm"
    template_name: str = "web/full/detail/group.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("tags", "links")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.seo_object = self.object
        now = timezone.now()
        events = list(
            Event.objects.filter(group=self.object)
            .select_related("group")
            .prefetch_related("tags")
            .order_by("start_datetime", "pk")
        )
        context.update(
            group_icon=get_icon_classes(self.object.icon),
            upcoming_events=[event for event in events if event.start_datetime >= now and not event.is_cancelled],
            past_events=[event for event in reversed(events) if event.start_datetime < now],
        )
        return context


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
                upcoming_event_count=Count(
                    "event",
                    filter=Q(event__start_datetime__gte=timezone.now(), event__status=Event.Status.ACTIVE),
                    distinct=True,
                )
            )
            .prefetch_related("tags")
            .order_by("-upcoming_event_count", "name", "pk")
        )
        if kwargs.get("display") == "marquee" or (
            not kwargs.get("display") and request.GET.get("display") == "marquee"
        ):
            kwargs["display"] = "minimal"
        return super().get(request, *args, **kwargs)

    def filter_by_query_params(self, parameters=None):
        """Preserve directory filters without relying on helper-specific signatures."""
        parameters = self.request.GET if parameters is None else parameters
        field_names = {field.name for field in TechGroup._meta.get_fields()}
        filters = {}
        for key, value in parameters.items():
            if key.split("__", 1)[0] not in field_names:
                continue
            if key.endswith("__in") and isinstance(value, str):
                value = [part.strip() for part in value.split(",") if part.strip()]
            elif value == "None":
                value = None
            elif value in ("True", "true", "TRUE"):
                value = True
            elif value in ("False", "false", "FALSE"):
                value = False
            filters[key] = value
        try:
            queryset = self.queryset.filter(**filters)
        except (FieldError, TypeError, ValueError):
            return self.queryset.none()
        return queryset.distinct() if "distinct" in parameters else queryset


class TechGroupModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying get details of a TechGroup instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/group_information.htm"
    modal_title: str = "Group details"
    template_name: str = "core/partials/modal_swap.htm"
    model = TechGroup


class CommunityGuideView(HtmxOptionView):
    """First-party guidance supported by enabled groups and actual upcoming events."""

    template_name = "web/full/custom/guide.html"
    htmx_template_name = "web/partials/custom/guide.htm"

    def get(self, request, *args, **kwargs):
        newcomer = request.resolver_match.url_name == "newcomer_guide"
        self.context = {
            "newcomer": newcomer,
            "guide_groups": TechGroup.objects.filter(enabled=True)
            .annotate(
                upcoming_event_count=Count(
                    "event",
                    filter=Q(event__start_datetime__gte=timezone.now(), event__status=Event.Status.ACTIVE),
                    distinct=True,
                )
            )
            .prefetch_related("tags")
            .order_by("name"),
            "guide_events": Event.objects.filter(
                status=Event.Status.ACTIVE, start_datetime__gte=timezone.now(), group__enabled=True
            )
            .select_related("group")
            .prefetch_related("tags")
            .order_by("start_datetime", "pk")[:6],
        }
        return super().get(request, *args, **kwargs)

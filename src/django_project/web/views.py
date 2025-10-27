from django.utils import timezone
from handyhelpers.views.calendar import HtmxCalendarView
from handyhelpers.views.htmx import (
    HtmxOptionDetailView,
    HtmxOptionMultiFilterView,
    HtmxOptionView,
    ModelDetailBootstrapModalView,
)
from web.models import Event, TechGroup


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


class TechEventView(HtmxOptionDetailView):
    """Render detail page for an Event instance"""

    model = Event
    htmx_template_name: str = "web/partials/detail/event.htm"
    template_name: str = "web/full/detail/event.html"


class TechEventsView(HtmxOptionMultiFilterView):
    """Render a list of Event instances"""

    htmx_minimal_wrapper_template_name: str = "web/partials/li/events.htm"
    htmx_list_wrapper_template_name: str = "web/partials/list/events.htm"
    htmx_template_name: str = "web/partials/li/events.htm"
    template_name: str = "web/full/list/events.html"

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
    queryset = TechGroup.objects.filter(enabled=True)
    template_name: str = "web/full/list/groups.html"


class TechGroupModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying get details of a TechGroup instance"""

    modal_button_submit = None
    modal_size: str = "modal-lg"
    modal_template: str = "web/partials/modal/group_information.htm"
    modal_title: str = "Group Info"
    model = TechGroup

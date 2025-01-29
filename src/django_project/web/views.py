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

    htmx_template_name = "web/partials/custom/about.htm"
    template_name = "web/full/custom/about.html"


class DevelopContentView(HtmxOptionView):
    """Render the 'development' page"""

    htmx_template_name = "web/partials/custom/develop.htm"
    template_name = "web/full/custom/develop.html"


class EventCalendarView(HtmxCalendarView):
    """Render a monthly calendar view of Event instances"""

    event_detail_url = "web:techevent_modal"
    event_model = Event
    event_model_date_field = "start_datetime"
    htmx_template_name = "web/partials/custom/calendar.htm"
    template_name = "web/full/custom/calendar.html"
    title = "Spokane Tech Event Calendar"


class IndexContentView(HtmxOptionView):
    """Render the index page"""

    htmx_template_name = "web/partials/custom/index.htm"
    template_name = "web/full/custom/index.html"

    def get(self, request):
        self.context = {
            "event_count": Event.objects.filter(start_datetime__gte=timezone.now()).count(),
            "group_count": TechGroup.objects.filter(enabled=True).count(),
        }
        return super().get(request)


class TechEventView(HtmxOptionDetailView):
    """Render detail page for an Event instance"""

    model = Event
    htmx_template_name = "web/partials/detail/event.htm"
    template_name = "web/full/detail/event.html"


class TechEventsView(HtmxOptionMultiFilterView):
    """Render a list of Event instances"""

    htmx_list_template_name = "web/partials/list/events.htm"
    htmx_list_wrapper_template_name = "web/partials/list/wrapper_list.htm"
    htmx_template_name = "web/partials/marquee/events.htm"
    queryset = Event.objects.filter(start_datetime__gte=timezone.now())
    template_name = "web/full/list/events.html"


class TechEventModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying details of an Event instance"""

    modal_button_submit = None
    modal_size = "modal-lg"
    modal_template = "web/partials/modal/event_information.htm"
    modal_title = "Event Info"
    model = Event


class TechGroupView(HtmxOptionDetailView):
    """Render detail page for a TechGroup instance"""

    model = TechGroup
    htmx_template_name = "web/partials/detail/group.htm"
    template_name = "web/full/detail/group.html"


class TechGroupsView(HtmxOptionMultiFilterView):
    """Render a list of TechGroup instances"""

    htmx_list_template_name = "web/partials/list/groups.htm"
    htmx_list_wrapper_template_name = "web/partials/list/wrapper_list.htm"
    htmx_template_name = "web/partials/marquee/groups.htm"
    queryset = TechGroup.objects.filter(enabled=True)
    template_name = "web/full/list/groups.html"


class TechGroupModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying get details of a TechGroup instance"""

    modal_button_submit = None
    modal_size = "modal-lg"
    modal_template = "web/partials/modal/group_information.htm"
    modal_title = "Group Info"
    model = TechGroup

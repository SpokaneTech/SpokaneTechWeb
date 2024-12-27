from django.utils import timezone
from handyhelpers.views.calendar import HtmxCalendarView
from handyhelpers.views.htmx import (
    HtmxOptionDetailView,
    HtmxOptionMultiFilterView,
    HtmxOptionView,
    ModelDetailBootstrapModalView,
)
from web.models import Event, TechGroup


class GetIndexContent(HtmxOptionView):
    """Render the index page"""

    htmx_template_name = "web/partials/custom/index.htm"
    template_name = "web/full/custom/index.html"


class GetAboutContent(HtmxOptionView):
    """Render the 'about' page"""

    htmx_template_name = "web/partials/custom/about.htm"
    template_name = "web/full/custom/about.html"


class EventCalendarView(HtmxCalendarView):
    """Render a monthly calendar view of events"""

    title = "Spokane Tech Event Calendar"
    event_model = Event
    event_model_date_field = "date_time"
    event_detail_url = "web:techevent_modal"
    htmx_template_name = "web/partials/custom/calendar.htm"
    template_name = "web/full/custom/calendar.html"


class GetTechEvent(HtmxOptionDetailView):
    """Get details of an Event instance"""

    model = Event
    htmx_template_name = "web/partials/detail/event.htm"
    template_name = "web/full/detail/event.html"


class GetTechEvents(HtmxOptionMultiFilterView):
    """Get a list of Event entries"""

    template_name = "web/full/list/events.html"
    htmx_template_name = "web/partials/marquee/events.htm"
    htmx_list_template_name = "web/partials/list/events.htm"
    queryset = Event.objects.filter(start_datetime__gte=timezone.now())
    htmx_list_wrapper_template_name = "web/partials/list/wrapper_list.htm"


class GetTechEventModal(ModelDetailBootstrapModalView):
    """Get details of an Event instance and display in a modal"""

    modal_button_submit = None
    modal_size = "modal-lg"
    modal_template = "web/partials/modal/event_information.htm"
    modal_title = "Event Info"
    model = Event


class GetTechGroup(HtmxOptionDetailView):
    """Get details of a TechGroup instance"""

    model = TechGroup
    htmx_template_name = "web/partials/detail/group.htm"
    template_name = "web/full/detail/group.html"


class GetTechGroups(HtmxOptionMultiFilterView):
    """Get a list of TechGroup entries"""

    template_name = "web/full/list/groups.html"
    htmx_template_name = "web/partials/marquee/groups.htm"
    htmx_list_template_name = "web/partials/list/groups.htm"
    queryset = TechGroup.objects.filter(enabled=True)
    htmx_list_wrapper_template_name = "web/partials/list/wrapper_list.htm"


class GetTechGroupModal(ModelDetailBootstrapModalView):
    """get details of a TechGroup instance and display in a modal"""

    modal_button_submit = None
    modal_template = "web/partials/modal/group_information.htm"
    modal_title = "Group Info"
    model = TechGroup

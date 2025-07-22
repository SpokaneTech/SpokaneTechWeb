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

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "Mobile" in user_agent:
            self.htmx_template_name = "web/partials/custom/calendar_mobile.htm"
        return super().get(request, *args, **kwargs)


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
    template_name = "web/full/list/events.html"

    def get(self, request, *args, **kwargs):
        self.queryset = Event.objects.filter(start_datetime__gte=timezone.now())
        return super().get(request, *args, **kwargs)


class TechEventModalView(ModelDetailBootstrapModalView):
    """Render Bootstrap 5 modal displaying details of an Event instance"""

    modal_button_submit = None
    modal_size = "modal-lg"
    modal_template = "web/partials/modal/event_information.htm"
    modal_title = "Event Info"
    model = Event

    def get(self, request, *args, **kwargs):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if "Mobile" in user_agent:
            self.modal_template = "web/partials/modal/event_information_modal.htm"
        return super().get(request, *args, **kwargs)


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


import requests
from django.conf import settings
from django.http import HttpResponse


def facebook_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Missing code", status=400)

    # Step 1: Exchange code for short-lived access token
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "redirect_uri": "http://localhost:8000/facebook/callback/",
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "code": code,
    }
    response = requests.get(token_url, params=params)
    data = response.json()
    short_token = data.get("access_token")

    if not short_token:
        return HttpResponse(f"Token exchange failed: {data}", status=500)

    # Step 2: Exchange short token for long-lived token
    long_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "fb_exchange_token": short_token,
    }
    long_response = requests.get(long_url, params=params)
    long_data = long_response.json()
    long_token = long_data.get("access_token")

    if not long_token:
        return HttpResponse(f"Long token exchange failed: {long_data}", status=500)

    return HttpResponse(f"✅ Long-lived token:<br><code>{long_token}</code>")


"""
https://www.facebook.com/v19.0/dialog/oauth?client_id=1049092166971471&redirect_uri=http://localhost:8000/facebook/callback/&scope=pages_manage_posts,pages_show_list&response_type=code&auth_type=rerequest

"""

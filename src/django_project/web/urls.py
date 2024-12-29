from django.urls import path, re_path
from web import views

app_name = "web"

urlpatterns = [
    path("", views.IndexContentView.as_view(), name="index"),
    path("index", views.IndexContentView.as_view(), name="index"),
    path("about", views.AboutContentView.as_view(), name="about"),
    path("calendar/<int:year>/<int:month>", views.EventCalendarView.as_view(), name="event_calendar"),
    path("events/<int:pk>", views.TechEventView.as_view(), name="get_event"),
    path("events/<int:pk>/modal", views.TechEventModalView.as_view(), name="techevent_modal"),
    re_path("^events/(?P<display>\w+)?$", views.TechEventsView.as_view(), name="get_events"),
    path("techgroups/<int:pk>", views.TechGroupView.as_view(), name="get_techgroup"),
    path("techgroups/<int:pk>/modal", views.TechGroupModalView.as_view(), name="techgroup_modal"),
    re_path("^techgroups/(?P<display>\w+)?$", views.TechGroupsView.as_view(), name="get_techgroups"),
]

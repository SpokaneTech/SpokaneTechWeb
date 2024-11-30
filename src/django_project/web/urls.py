from django.urls import path, re_path
from web import views

app_name = "web"

urlpatterns = [
    path("", views.GetIndexContent.as_view(), name="index"),
    path("index", views.GetIndexContent.as_view(), name="index"),
    path("about", views.GetAboutContent.as_view(), name="about"),
    path("calendar/<int:year>/<int:month>", views.EventCalendarView.as_view(), name="event_calendar"),
    path("events/<int:pk>", views.GetTechEvent.as_view(), name="get_event"),
    path("events/<int:pk>/details", views.GetTechEventModal.as_view(), name="techevent_modal"),
    re_path("^events/(?P<display>\w+)?$", views.GetTechEvents.as_view(), name="get_events"),
    path("techgroups/<int:pk>", views.GetTechGroup.as_view(), name="get_techgroup"),
    path("techgroups/<int:pk>/details", views.GetTechGroupModal.as_view(), name="techgroup_modal"),
    re_path("^techgroups/(?P<display>\w+)?$", views.GetTechGroups.as_view(), name="get_techgroups"),
]

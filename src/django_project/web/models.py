from __future__ import annotations

from django.db import models
from django.urls import reverse
from handyhelpers.models import HandyHelperBaseModel


class Event(HandyHelperBaseModel):
    """An event on a specific day and time"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField(
        auto_now=False, auto_now_add=False, help_text="date and time the event starts"
    )
    end_datetime = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, help_text="date and time the event ends"
    )
    location_name = models.CharField(
        max_length=64,
        blank=True,
        help_text="name of location where this event is being hosted",
    )
    location_address = models.CharField(
        max_length=256,
        blank=True,
        help_text="address of location where this event is being hosted",
    )
    map_link = models.URLField(
        blank=True,
        help_text="link to a map showing the location of the event",
    )
    url = models.URLField(
        blank=True,
        help_text="URL to the event details",
    )
    social_platform_id = models.CharField(
        max_length=128,
        blank=True,
        help_text="unique identifier provided by the social platform hosting the event",
    )
    group = models.ForeignKey("TechGroup", blank=True, null=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField("Tag", blank=True)
    image = models.ImageField(upload_to="tech_events/", blank=True, null=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("web:get_event", kwargs={"pk": self.pk})


class Link(HandyHelperBaseModel):
    """A link to a resource associated with a TechGroup or Event"""

    name = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    url = models.URLField()

    def __str__(self):
        return self.url


class SocialPlatform(HandyHelperBaseModel):
    """The social platform (such as Meetup) that hosts the group and events"""

    name = models.CharField(max_length=64, unique=True, help_text="service where this tech group is hosted")
    enabled = models.BooleanField(default=True)
    base_url = models.URLField(blank=True, help_text="base url of provider")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Tag(HandyHelperBaseModel):
    """A tag that describes attributes of a Event or a TechGroup"""

    value = models.CharField(max_length=64, unique=True, null=False)

    class Meta:
        ordering = ["value"]

    def __str__(self) -> str:
        return self.value


class TechGroup(HandyHelperBaseModel):
    """A group that organizes events"""

    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    platform = models.ForeignKey("SocialPlatform", on_delete=models.CASCADE)
    icon = models.CharField(
        max_length=255,
        blank=True,
        help_text="Font Awesome CSS icon class(es) to represent the group.",
    )
    tags = models.ManyToManyField("Tag", blank=True)
    links = models.ManyToManyField("Link", blank=True)
    image = models.ImageField(upload_to="techgroups/", blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("web:get_techgroup", kwargs={"pk": self.pk})

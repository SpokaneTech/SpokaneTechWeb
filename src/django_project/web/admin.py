from django.contrib import admin

# import models
from web.models import Event, Link, SocialPlatform, Tag, TechGroup


class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "value", "created_at", "updated_at"]
    search_fields = ["id", "value"]


class LinkAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "url", "created_at", "updated_at"]
    search_fields = ["id", "name", "description", "url"]


class SocialPlatformAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "enabled", "base_url", "created_at", "updated_at"]
    search_fields = ["id", "name", "base_url"]
    list_filter = ["enabled"]


class TechGroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "enabled", "platform", "icon", "image", "created_at", "updated_at"]
    search_fields = ["id", "name", "description", "icon", "image"]
    list_filter = ["enabled", "platform"]


class EventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
        "updated_at",
        "name",
        "description",
        "start_datetime",
        "end_datetime",
        "location_name",
        "location_address",
        "map_link",
        "url",
        "social_platform_id",
        "group",
        "image",
    ]
    search_fields = [
        "id",
        "name",
        "description",
        "location_name",
        "location_address",
        "map_link",
        "url",
        "social_platform_id",
        "image",
    ]
    list_filter = ["group"]


# register models
admin.site.register(Tag, TagAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(SocialPlatform, SocialPlatformAdmin)
admin.site.register(TechGroup, TechGroupAdmin)
admin.site.register(Event, EventAdmin)

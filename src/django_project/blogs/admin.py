# import models
from __future__ import annotations

from django.contrib import admin

from blogs.models import BlogPlatform, BlogPost, BlogSeries, BlogTag


class BlogPlatformAdmin(admin.ModelAdmin):
    list_display: tuple[str, ...] = ("id", "created_at", "updated_at", "enabled", "name", "website_url")
    search_fields: tuple[str, ...] = ("id", "name", "website_url")
    list_filter: tuple[str, ...] = ("enabled",)


class BlogSeriesAdmin(admin.ModelAdmin):
    list_display: tuple[str, ...] = ("id", "created_at", "updated_at", "name", "description")
    search_fields: tuple[str, ...] = ("id", "name", "description")
    list_filter: tuple[()] = ()


class BlogPostAdmin(admin.ModelAdmin):
    list_display: tuple[str, ...] = (
        "id",
        "created_at",
        "updated_at",
        "platform",
        "title",
        "description",
        "url",
        "image",
        "author",
        "series",
    )
    search_fields: tuple[str, ...] = ("id", "title", "description", "url", "image", "author")
    list_filter: tuple[str, ...] = ("platform", "series")


class BlogTagAdmin(admin.ModelAdmin):
    list_display: tuple[str, ...] = ("id", "created_at", "updated_at", "value")
    search_fields: tuple[str, ...] = ("id", "value")
    list_filter: tuple[()] = ()


# register models
admin.site.register(BlogPlatform, BlogPlatformAdmin)
admin.site.register(BlogSeries, BlogSeriesAdmin)
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(BlogTag, BlogTagAdmin)

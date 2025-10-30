# import models
from blogs.models import BlogPlatform, BlogPost, BlogSeries
from django.contrib import admin


class BlogPlatformAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "created_at", "updated_at", "enabled", "name", "website_url"]
    search_fields: list[str] = ["id", "name", "website_url"]
    list_filter: list[str] = ["enabled"]


class BlogSeriesAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "created_at", "updated_at", "name", "description"]
    search_fields: list[str] = ["id", "name", "description"]
    list_filter: list = []


class BlogPostAdmin(admin.ModelAdmin):
    list_display: list[str] = [
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
    ]
    search_fields: list[str] = ["id", "title", "description", "url", "image", "author"]
    list_filter: list[str] = ["platform", "series"]


# register models
admin.site.register(BlogPlatform, BlogPlatformAdmin)
admin.site.register(BlogSeries, BlogSeriesAdmin)
admin.site.register(BlogPost, BlogPostAdmin)

from django.contrib import admin

# import models
from blogs.models import (BlogPlatform,
                          BlogSeries,
                          BlogPost
                          )


class BlogPlatformAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at', 'enabled', 'name', 'website_url']
    search_fields = ['id', 'name', 'website_url']
    list_filter = ['enabled']


class BlogSeriesAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at', 'name', 'description']
    search_fields = ['id', 'name', 'description']
    list_filter = []


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at', 'platform', 'title', 'description', 'url', 'image', 'author', 'series']
    search_fields = ['id', 'title', 'description', 'url', 'image', 'author']
    list_filter = ['platform', 'series']


# register models
admin.site.register(BlogPlatform, BlogPlatformAdmin)
admin.site.register(BlogSeries, BlogSeriesAdmin)
admin.site.register(BlogPost, BlogPostAdmin)

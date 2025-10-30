from django.db.models.manager import BaseManager
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from blogs.models import BlogPost


class BlogPostListView(View):
    def get(self, request) -> HttpResponse:
        queryset: BaseManager[BlogPost] = BlogPost.objects.filter(platform__enabled=True).order_by("created_at")
        return render(request, "blogs/partials/list/blog_posts.htm", {"queryset": queryset})

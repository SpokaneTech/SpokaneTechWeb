from blogs import views
from django.urls import path
from django.urls.resolvers import URLPattern

app_name = "blogs"


urlpatterns: list[URLPattern] = [
    path("blog_posts/", views.BlogPostListView.as_view(), name="blog_posts"),
]

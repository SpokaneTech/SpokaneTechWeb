from django.db import models
from handyhelpers.models import HandyHelperBaseModel


# Create your models here.
class BlogPlatform(HandyHelperBaseModel):
    enabled = models.BooleanField(default=True)
    name = models.CharField(max_length=100, unique=True)
    website_url = models.URLField()

    def __str__(self) -> str:
        return self.name


class BlogSeries(HandyHelperBaseModel):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class BlogPost(HandyHelperBaseModel):
    platform = models.ForeignKey(BlogPlatform, on_delete=models.CASCADE, related_name="blogs")
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField()
    image = models.ImageField(upload_to="blog_images/", null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    series = models.ForeignKey(BlogSeries, on_delete=models.SET_NULL, null=True, blank=True, related_name="blogs")

    def __str__(self) -> str:
        return self.title

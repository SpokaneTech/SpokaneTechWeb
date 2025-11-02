from django.db import models
from handyhelpers.models import HandyHelperBaseModel


# Create your models here.
class BlogPlatform(HandyHelperBaseModel):
    """
    Represents a blogging platform with its name, website URL, and enabled status.
    """

    enabled = models.BooleanField(default=True)
    name = models.CharField(max_length=100, unique=True)
    website_url = models.URLField()

    def __str__(self) -> str:
        return self.name


class BlogSeries(HandyHelperBaseModel):
    """
    Represents a series of blog posts with a unique name and optional description.
    """

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class BlogPost(HandyHelperBaseModel):
    """
    Represents a blog post with details such as platform, title, description, URL, image, author, series, and tags.
    Attributes:
        platform (ForeignKey): The platform where the blog post is published.
        title (CharField): The title of the blog post.
        description (TextField): A detailed description of the blog post.
        url (URLField): The URL of the blog post.
        image (ImageField): An optional image associated with the blog post.
        author (CharField): The author of the blog post (optional).
        series (ForeignKey): The series to which the blog post belongs (optional).
        tags (ManyToManyField): Tags associated with the blog post (optional).
    """

    platform = models.ForeignKey(BlogPlatform, on_delete=models.CASCADE, related_name="blogs")
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField()
    image = models.ImageField(upload_to="blog_images/", null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    series = models.ForeignKey(BlogSeries, on_delete=models.SET_NULL, null=True, blank=True, related_name="blogs")
    tags = models.ManyToManyField("BlogTag", blank=True)

    def __str__(self) -> str:
        return self.title


class BlogTag(HandyHelperBaseModel):
    """
    Represents a tag that can be associated with other entities.
    Attributes:
        value (str): The unique name of the tag, limited to 64 characters.
    """

    value = models.CharField(max_length=64, unique=True, null=False)

    class Meta:
        ordering = ["value"]

    def __str__(self) -> str:
        return self.value

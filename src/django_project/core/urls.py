"""spokanetech URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from core.views import robots_txt
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django provided URLs
    path("console/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("robots.txt", robots_txt),
    # 3rd party URLs
    path("handyhelpers/", include("handyhelpers.urls")),
    # app URLs
    path("", include("web.urls", namespace="web")),
]

if settings.DEBUG:
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )  # pragma: no cover

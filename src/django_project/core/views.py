from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    return HttpResponse(robots_txt_content, content_type="text/plain")


robots_txt_content = """\
User-Agent: *
Disallow: /__debug__/
Disallow: /accounts/
Disallow: /admin/
"""

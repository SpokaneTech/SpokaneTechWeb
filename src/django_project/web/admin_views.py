# web/admin_views.py
import hashlib
import hmac

import requests
from django.conf import settings
from django.http import HttpResponse
from django.template.response import TemplateResponse


def facebook_post_view(request):
    message = request.GET.get("message", "Hello from Django Admin!")
    user_token = getattr(settings, "FACEBOOK_LONG_LIVED_USER_TOKEN", None)
    app_secret = getattr(settings, "FACEBOOK_APP_SECRET", None)

    if not user_token or not app_secret:
        return HttpResponse("Missing FACEBOOK_LONG_LIVED_USER_TOKEN or FACEBOOK_APP_SECRET in settings.py", status=400)

    # Compute appsecret_proof
    appsecret_proof = hmac.new(app_secret.encode("utf-8"), user_token.encode("utf-8"), hashlib.sha256).hexdigest()

    # Get Page Access Token
    resp = requests.get(
        "https://graph.facebook.com/v19.0/me/accounts",
        params={"access_token": user_token, "appsecret_proof": appsecret_proof},
    )
    page_data = resp.json()

    if "data" not in page_data or not page_data["data"]:
        return HttpResponse(f"Error retrieving pages: {page_data}", status=400)

    page = page_data["data"][0]
    page_id = page["id"]
    page_token = page["access_token"]

    # Make the post
    post_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{page_id}/feed", data={"message": message, "access_token": page_token}
    )
    result = post_resp.json()

    return TemplateResponse(
        request, "admin/facebook_post.html", {"page_id": page_id, "result": result, "message": message}
    )

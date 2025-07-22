import hashlib
import hmac

import requests
from django.conf import settings


def run():
    print("🚀 Starting Facebook post script...")

    page_id = getattr(settings, "FACEBOOK_PAGE_ID", None)
    user_token = getattr(settings, "FACEBOOK_LONG_LIVED_USER_TOKEN", None)
    app_secret = getattr(settings, "FACEBOOK_APP_SECRET", None)
    message = "📣 Hello from Django runscript!"

    if not user_token or not app_secret:
        print("❌ Missing FACEBOOK_LONG_LIVED_USER_TOKEN or FACEBOOK_APP_SECRET in settings.py")
        return

    # Step 1: Generate appsecret_proof
    appsecret_proof = hmac.new(app_secret.encode("utf-8"), user_token.encode("utf-8"), hashlib.sha256).hexdigest()

    # Step 2: Get Page Access Token
    page_token_url = f"https://graph.facebook.com/v19.0/{page_id}"
    token_resp = requests.get(
        page_token_url,
        params={
            "fields": "access_token",
            "access_token": user_token,
            "appsecret_proof": appsecret_proof,
        },
    )
    page_token_data = token_resp.json()
    print("🔍 Page token response:", page_token_data)

    page_token = page_token_data.get("access_token")
    if not page_token:
        print("❌ Failed to get Page Access Token.")
        return

    # Step 3: Post to Page Feed

    # Generate appsecret_proof from page_token (not user token)
    page_appsecret_proof = hmac.new(app_secret.encode("utf-8"), page_token.encode("utf-8"), hashlib.sha256).hexdigest()

    post_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    post_resp = requests.post(
        post_url,
        data={
            "message": message,
            "access_token": page_token,
            "appsecret_proof": page_appsecret_proof,
        },
        timeout=15,
    )
    post_result = post_resp.json()
    print("📤 Post response:", post_result)

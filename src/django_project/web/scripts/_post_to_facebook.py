def run():
    import hashlib
    import hmac

    import requests
    from django.conf import settings

    print("Starting Facebook post script...")

    user_token = getattr(settings, "FACEBOOK_LONG_LIVED_USER_TOKEN", None)
    app_secret = getattr(settings, "FACEBOOK_APP_SECRET", None)
    message = "Hello from Django runscript!"

    if not user_token or not app_secret:
        print("ERROR: FACEBOOK_LONG_LIVED_USER_TOKEN or FACEBOOK_APP_SECRET missing in settings.py")
        return

    # Generate appsecret_proof
    appsecret_proof = hmac.new(app_secret.encode("utf-8"), user_token.encode("utf-8"), hashlib.sha256).hexdigest()

    try:
        # Step 1: Get Page Access Token
        page_resp = requests.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={
                "access_token": user_token,
                "appsecret_proof": appsecret_proof,
            },
        )
        if page_resp.status_code != 200:
            print(f"Error fetching pages: HTTP {page_resp.status_code}")
            print(page_resp.text)
            return

        page_data = page_resp.json()
        print("Fetched pages:", page_data)

        if "data" not in page_data or not page_data["data"]:
            print(f"Failed to get pages: {page_data}")
            return

        page = page_data["data"][0]
        page_id = page["id"]
        page_token = page["access_token"]

        print(f"Using page '{page['name']}' (ID: {page_id})")

        # Step 2: Post message to the page feed
        post_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/feed",
            data={
                "message": message,
                "access_token": page_token,
            },
        )

        post_result = post_resp.json()
        print(f"Post response: {post_result}")

        if "id" in post_result:
            print(f"Success! Post ID: {post_result['id']}")
        else:
            print(f"Failed to create post: {post_result}")

    except Exception as e:
        print(f"Exception occurred: {e}")

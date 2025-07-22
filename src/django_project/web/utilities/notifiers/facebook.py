import requests


class FacebookPageClient:
    def __init__(
        self,
        access_token: str,
        page_id: str,
        graph_api_version: str = "v19.0",
    ) -> None:
        self.access_token: str = access_token
        self.page_id: str = page_id
        self.post_url: str = f"https://graph.facebook.com/{graph_api_version}/{page_id}/feed"

    def post_message(self, message: str) -> requests.Response:
        print(f"Attempting to post to Facebook Page ID: {self.page_id}")
        print(f"Message: '{message}'")

        message = "Hello Spokane Tech! This is an automated test post from Python."

        payload: dict[str, str] = {"message": message, "access_token": self.access_token}

        try:
            response: requests.Response = requests.post(self.post_url, data=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            response_data = response.json()
            print("\nPost successful!")
            print(f"Facebook API Response: {response_data}")
            if "id" in response_data:
                print(f"Post ID: {response_data['id']}")
                # Construct a direct link to the post (may vary slightly based on Facebook's UI)
                post_link = f"https://www.facebook.com/{response_data['id']}"
                print(f"You can view the post at: {post_link}")

        except requests.exceptions.HTTPError as http_err:
            print(f"\nHTTP error occurred: {http_err}")
            if response is not None:
                print(f"Response content: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"\nConnection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"\nTimeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"\nAn unexpected request error occurred: {req_err}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

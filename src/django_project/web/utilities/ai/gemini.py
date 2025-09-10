import json
from typing import Any

import requests
from django.conf import settings


def generate_post_content(prompt: str, model: str = "gemini-2.5-flash-lite") -> str:
    """
    Generates content for a post using the Gemini API based on the provided prompt.
    Args:
        prompt (str): The input text prompt to generate content from.
        model (str, optional): The Gemini model to use for generation. Defaults to "gemini-2.5-flash-lite".
    Returns:
        str: The generated content as a string.
    Raises:
        ValueError: If the GEMINI_API_KEY is not set in settings or if the API response format is unexpected.
        requests.HTTPError: If the HTTP request to the Gemini API fails.
    """

    gemini_api_key: str = getattr(settings, "GEMINI_API_KEY", "")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set in settings.")

    url: str = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload: str = json.dumps({"contents": [{"parts": [{"text": prompt}]}]})
    headers: dict[str, str] = {"x-goog-api-key": gemini_api_key, "Content-Type": "application/json"}
    response: requests.Response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    data: Any = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ValueError("Unexpected response format from Gemini API.")

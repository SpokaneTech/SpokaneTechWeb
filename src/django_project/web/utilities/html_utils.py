import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def fetch_content(url, timeout=30) -> bytes | Any:
    """fetch html content from a url using requests

    Args:
        url (str): url to fetch content from
        timeout (int, optional): timeout in seconds. Defaults to 30.

    Raises:
        Exception: if the response status code is not 200

    Returns:
        str: response text from the url
    """
    headers = {"Cache-Control": "no-cache", "Pragma": "no-cache", "User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch content from {url}: {response.status_code}")


def fetch_content_with_playwright(url, retries=3, timeout=30000):
    """fetch html content from a url using playwright

    Args:
        url (str): url to fetch content from

    Returns:
        str: response text from the url

    <main id="main" class="flex flex-grow flex-col items-center justify-between">
    """
    attempt = 0
    while attempt < retries:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url, wait_until="networkidle", timeout=timeout)
                html_content = page.content()
                browser.close()

            return html_content
        except Exception as e:
            print(f"Error: {e}. Retrying... ({attempt + 1}/{retries})")
            attempt += 1
            if attempt == retries:
                print("Max retries reached. Could not fetch the content.")
                return ""
            time.sleep(2)


def find_target(url, parent="ul", classes="flex w-full flex-col space-y-5 px-4 md:px-0", max_retries=3):
    """find the target ul element in the html content

    Args:
        url (str): url to fetch content from
        parent (str, optional): parent html element to find. Defaults to "ul".
        classes (str, optional): css classes to use in element search. Defaults to "flex w-full flex-col space-y-5 px-4 md:px-0".
        max_retries (int, optional): max count of retries to attempt. Defaults to 3.

    Raises:
        Exception: if the target element is not found after max_retries

    Returns:
        str: html content of the target element
    """
    retries = 0
    while retries < max_retries:
        print(f"Attempt {retries + 1}/{max_retries}: Fetching HTML content...")
        html_content = fetch_content(url)
        soup = BeautifulSoup(html_content, "html.parser")
        target_ul = soup.find(parent, class_=classes)
        if target_ul:
            return target_ul
        retries += 1
        print(f"Retry {retries}/{max_retries}: target_ul not found. Retrying in {1 + retries} seconds...")
        time.sleep(1 + retries)

    raise Exception("target_ul not found after maximum retries")

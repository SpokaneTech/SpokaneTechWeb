"""Published policies remain accessible and match the repository's policy text."""

import os
import re
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse


class PolicyPageTests(TestCase):
    def test_full_and_htmx_policies_match_repository_text_and_links(self):
        repository = Path(__file__).resolve().parents[3].parent.parent
        for name, filename in (("privacy", "PRIVACY_POLICY.md"), ("terms", "TERMS_OF_SERVICE.md")):
            markdown = (repository / ".github" / filename).read_text()
            lines = [
                line.removeprefix("## ")
                for line in markdown.splitlines()
                if line and not line.startswith(("# ", "Last updated:"))
            ]
            expected_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", " ".join(lines))
            expected_links = [
                url.replace("https://www.spokanetech.org/privacy/", "/privacy/")
                for url in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown)
            ]
            for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
                with self.subTest(policy=name, headers=headers):
                    response = self.client.get(reverse(f"web:{name}"), **headers)
                    self.assertEqual(response.status_code, 200)
                    page = BeautifulSoup(response.content, "html.parser")
                    content = page.select_one(".st-policy-content")
                    self.assertIsNotNone(content)
                    actual_text = " ".join(block.get_text().strip() for block in content.select("h2, p"))
                    self.assertEqual(" ".join(actual_text.split()), " ".join(expected_text.split()))
                    self.assertEqual([link["href"] for link in content.select("a")], expected_links)
                    self.assertEqual(len(page.select("h1")), 1)
                    updated = next(line for line in markdown.splitlines() if line.startswith("Last updated:"))
                    self.assertContains(response, updated)
                    self.assertEqual(bool(page.select("html")), not bool(headers))

    def test_footer_links_to_both_policies(self):
        response = self.client.get(reverse("web:about"))
        footer = BeautifulSoup(response.content, "html.parser").select_one("footer")
        links = {link.get("href") for link in footer.select("a")}
        self.assertIn(reverse("web:privacy"), links)
        self.assertIn(reverse("web:terms"), links)

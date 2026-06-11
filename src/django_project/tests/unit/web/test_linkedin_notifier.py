import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

from web.utilities.notifiers.linkedin import LinkedInOrganizationClient


class DummyCredentialManager:
    def __init__(self, credential):
        self.credential = credential

    def select_for_update(self):
        return self

    def get(self, pk):
        return self.credential


class DummyCredential:
    objects = None

    def __init__(self):
        self.pk = 1
        self.access_token = "old-token"
        self.refresh_token = "refresh-token"
        self.access_token_expires_at = None
        self.refresh_token_expires_at = None
        self.save = Mock()


class LinkedInOrganizationClientTests(unittest.TestCase):
    def build_client(self, env_path: str | None = None, access_token: str | None = "old-token") -> LinkedInOrganizationClient:
        return LinkedInOrganizationClient(
            access_token=access_token,
            organization_urn="urn:li:organization:107506588",
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="refresh-token",
            env_path=env_path,
        )

    def test_refresh_access_token_updates_settings_and_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_env = Path(temp_dir) / ".env.test"
            temp_env.write_text(
                'LINKEDIN_ACCESS_TOKEN="old-token"\nLINKEDIN_REFRESH_TOKEN="refresh-token"\n',
                encoding="utf-8",
            )
            client = self.build_client(env_path=str(temp_env))

            response = Mock()
            response.json.return_value = {
                "access_token": "new-token",
                "refresh_token": "new-refresh-token",
            }
            response.raise_for_status.return_value = None

            with (
                patch("web.utilities.notifiers.linkedin.requests.post", return_value=response) as mock_post,
                patch("web.utilities.notifiers.linkedin.settings") as mock_settings,
            ):
                client.refresh_access_token()

            self.assertEqual(client.access_token, "new-token")
            self.assertEqual(client.refresh_token, "new-refresh-token")
            self.assertIn('LINKEDIN_ACCESS_TOKEN="new-token"', temp_env.read_text(encoding="utf-8"))
            self.assertIn('LINKEDIN_REFRESH_TOKEN="new-refresh-token"', temp_env.read_text(encoding="utf-8"))
            mock_post.assert_called_once()
            self.assertEqual(mock_settings.LINKEDIN_ACCESS_TOKEN, "new-token")
            self.assertEqual(mock_settings.LINKEDIN_REFRESH_TOKEN, "new-refresh-token")

    def test_post_retries_once_after_auth_failure(self):
        client = self.build_client()

        auth_failure_response = Mock(status_code=401)
        auth_failure_response.raise_for_status.side_effect = requests.HTTPError(response=auth_failure_response)  # type: ignore[name-defined]

        refresh_response = Mock()
        refresh_response.json.return_value = {
            "access_token": "new-token",
            "refresh_token": "new-refresh-token",
        }
        refresh_response.raise_for_status.return_value = None

        success_response = Mock(status_code=201)
        success_response.raise_for_status.return_value = None

        with (
            patch(
                "web.utilities.notifiers.linkedin.requests.post",
                side_effect=[auth_failure_response, refresh_response, success_response],
            ) as mock_post,
            patch("web.utilities.notifiers.linkedin.settings"),
        ):
            response = client.post_organization_post("hello world")

        self.assertIs(response, success_response)
        self.assertEqual(client.access_token, "new-token")
        self.assertEqual(mock_post.call_count, 3)

    def test_refresh_access_token_updates_db_credential_when_present(self):
        credential = DummyCredential()
        credential.__class__.objects = DummyCredentialManager(credential)

        client = LinkedInOrganizationClient(
            access_token="old-token",
            organization_urn="urn:li:organization:107506588",
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="refresh-token",
            credential=credential,
        )

        refresh_response = Mock()
        refresh_response.json.return_value = {
            "access_token": "new-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
            "refresh_token_expires_in": 7200,
        }
        refresh_response.raise_for_status.return_value = None

        with (
            patch("web.utilities.notifiers.linkedin.requests.post", return_value=refresh_response),
            patch("web.utilities.notifiers.linkedin.settings"),
        ):
            client.refresh_access_token()

        self.assertEqual(credential.access_token, "new-token")
        self.assertEqual(credential.refresh_token, "new-refresh-token")
        credential.save.assert_called_once()

    def test_missing_tokens_can_be_bootstrapped_from_refresh_credentials(self):
        client = self.build_client(access_token=None)

        refresh_response = Mock()
        refresh_response.json.return_value = {
            "access_token": "new-token",
            "refresh_token": "new-refresh-token",
        }
        refresh_response.raise_for_status.return_value = None

        success_response = Mock(status_code=201)
        success_response.raise_for_status.return_value = None

        with (
            patch(
                "web.utilities.notifiers.linkedin.requests.post",
                side_effect=[refresh_response, success_response],
            ),
            patch("web.utilities.notifiers.linkedin.settings"),
        ):
            client.post_organization_post("hello world")

        self.assertEqual(client.access_token, "new-token")

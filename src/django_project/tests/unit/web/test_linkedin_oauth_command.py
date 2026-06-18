import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

from web.management.commands.linkedin_oauth import Command


class LinkedInOAuthCommandTests(unittest.TestCase):
    def test_show_url_outputs_authorization_url(self):
        command = Command()
        command.stdout = Mock()

        with (
            patch("web.management.commands.linkedin_oauth.apps.get_model") as mock_get_model,
            patch("web.management.commands.linkedin_oauth.settings") as mock_settings,
            patch("web.management.commands.linkedin_oauth.LinkedInOrganizationClient") as mock_client_class,
        ):
            mock_settings.LINKEDIN_CLIENT_ID = "client-id"
            mock_settings.LINKEDIN_CLIENT_SECRET = "client-secret"
            mock_settings.LINKEDIN_ACCESS_TOKEN = None
            mock_settings.LINKEDIN_ORGANIZATION_URN = "urn:li:organization:107506588"
            mock_settings.LINKEDIN_REFRESH_TOKEN = None
            mock_settings.ENV_PATH = "/tmp/.env.test"

            mock_credential = Mock(access_token=None, refresh_token=None)
            mock_get_model.return_value.objects.get_or_create.return_value = (mock_credential, True)

            mock_client = mock_client_class.return_value
            mock_client.build_authorization_url.return_value = "https://www.linkedin.com/oauth/v2/authorization?x=1"

            command.handle(redirect_uri="https://example.com/callback", scope=command.default_scope, state=None, code=None)

        command.stdout.write.assert_any_call("Open this URL in a browser and complete the LinkedIn consent flow:")
        command.stdout.write.assert_any_call("https://www.linkedin.com/oauth/v2/authorization?x=1")

    def test_code_exchange_stores_tokens(self):
        command = Command()
        command.stdout = Mock()

        with (
            patch("web.management.commands.linkedin_oauth.apps.get_model") as mock_get_model,
            patch("web.management.commands.linkedin_oauth.settings") as mock_settings,
            patch("web.management.commands.linkedin_oauth.LinkedInOrganizationClient") as mock_client_class,
        ):
            mock_settings.LINKEDIN_CLIENT_ID = "client-id"
            mock_settings.LINKEDIN_CLIENT_SECRET = "client-secret"
            mock_settings.LINKEDIN_ACCESS_TOKEN = None
            mock_settings.LINKEDIN_ORGANIZATION_URN = "urn:li:organization:107506588"
            mock_settings.LINKEDIN_REFRESH_TOKEN = None
            mock_settings.ENV_PATH = "/tmp/.env.test"

            mock_credential = Mock(access_token=None, refresh_token=None)
            mock_get_model.return_value.objects.get_or_create.return_value = (mock_credential, True)

            mock_client = mock_client_class.return_value
            mock_client.exchange_authorization_code.return_value = {
                "access_token": "new-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 5184000,
                "refresh_token_expires_in": 31536000,
            }

            command.handle(
                redirect_uri="https://example.com/callback",
                scope=command.default_scope,
                state=None,
                code="auth-code",
                show_url=False,
            )

        mock_client.exchange_authorization_code.assert_called_once_with(
            code="auth-code",
            redirect_uri="https://example.com/callback",
        )

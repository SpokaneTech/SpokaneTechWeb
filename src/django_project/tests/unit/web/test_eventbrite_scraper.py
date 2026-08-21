import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import django

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")

django.setup()

from web.utilities.scrapers.eventbrite import get_events_for_organization


class TestGetEventsForOrganization:
    @patch("web.utilities.scrapers.eventbrite.requests.get")
    @patch("web.utilities.scrapers.eventbrite.timezone.now")
    def test_uses_configured_lookahead_window(self, mock_now, mock_get):
        mock_now.return_value = datetime(2026, 8, 21, 7, 11, 15, tzinfo=UTC)
        response = Mock()
        response.json.return_value = {"events": [{"id": "evt_123"}]}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with patch("web.utilities.scrapers.eventbrite.settings.EVENTBRITE_API_KEY", "token", create=True):
            with patch(
                "web.utilities.scrapers.eventbrite.settings.EVENTBRITE_EVENT_LOOKAHEAD_DAYS",
                60,
                create=True,
            ):
                events = get_events_for_organization("637389713")

        assert events == [{"id": "evt_123"}]
        mock_get.assert_called_once_with(
            "https://www.eventbriteapi.com/v3/organizers/637389713/events/"
            "?start_date.range_start=2026-08-21T07:11:15Z&start_date.range_end=2026-10-20T07:11:15Z",
            headers={"Authorization": "Bearer token"},
            timeout=15,
        )

    @patch("web.utilities.scrapers.eventbrite.requests.get")
    @patch("web.utilities.scrapers.eventbrite.timezone.now")
    def test_explicit_age_overrides_configured_lookahead(self, mock_now, mock_get):
        mock_now.return_value = datetime(2026, 8, 21, 7, 11, 15, tzinfo=UTC)
        response = Mock()
        response.json.return_value = {"events": [{"id": "evt_456"}]}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with patch("web.utilities.scrapers.eventbrite.settings.EVENTBRITE_API_KEY", "token", create=True):
            with patch(
                "web.utilities.scrapers.eventbrite.settings.EVENTBRITE_EVENT_LOOKAHEAD_DAYS",
                60,
                create=True,
            ):
                events = get_events_for_organization("637389713", age=14)

        assert events == [{"id": "evt_456"}]
        mock_get.assert_called_once_with(
            "https://www.eventbriteapi.com/v3/organizers/637389713/events/"
            "?start_date.range_start=2026-08-21T07:11:15Z&start_date.range_end=2026-09-04T07:11:15Z",
            headers={"Authorization": "Bearer token"},
            timeout=15,
        )

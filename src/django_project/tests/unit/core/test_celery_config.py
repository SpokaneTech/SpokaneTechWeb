import importlib
import os
import ssl
from pathlib import Path
from unittest.mock import MagicMock, patch

import django

BASE_DIR = Path(__file__).parents[4]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", f"{BASE_DIR}/envs/.env.test")
django.setup()


@patch("celery.Celery")
@patch("django.conf.settings", new_callable=lambda: MagicMock(CELERY_USE_SSL=True))
def test_celery_app_initialization_with_ssl(mock_settings, mock_celery):
    """Test that Celery app initializes with SSL settings if CELERY_USE_SSL is True."""
    import core.celery
    from core.celery import celery_app

    importlib.reload(core.celery)

    # Verify that Celery was called with the expected arguments
    mock_celery.assert_called_once_with(
        "core",
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
    )

    # Verify that the resulting app has the expected properties/methods (mocked)
    assert hasattr(celery_app, "autodiscover_tasks")  # Example property


@patch("celery.Celery")
@patch("django.conf.settings", new_callable=lambda: MagicMock(CELERY_USE_SSL=False))
def test_celery_app_initialization_without_ssl(mock_settings, mock_celery):
    """Test that Celery app initializes without SSL settings if CELERY_USE_SSL is False."""
    # Reload the core.celery module after patching Celery
    import core.celery

    importlib.reload(core.celery)

    # Assert that Celery was called with the expected arguments
    mock_celery.assert_called_once_with("core")

    # Optionally check redis_backend_use_ssl and broker_use_ssl are absent
    mock_celery.return_value.config_from_object.assert_called_once_with(mock_settings)


def test_debug_task():
    """Test the debug_task function."""
    import core.celery

    importlib.reload(core.celery)

    output = core.celery.debug_task.apply()
    assert output.status == "SUCCESS"
    assert output.successful() == True


def test_debug_task_response(capsys):
    """Test the response from the debug_task."""
    import core.celery

    importlib.reload(core.celery)

    args = ["arg1", "arg2"]
    kwargs = {"key": "value"}
    output = core.celery.debug_task.apply(args=args, kwargs=kwargs)
    captured = capsys.readouterr()
    assert str(args) in captured.out
    assert str(kwargs) in captured.out
    assert output.status == "SUCCESS"

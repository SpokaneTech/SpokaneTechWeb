"""All entry points use the required encryption dependency, never a plaintext shim."""

import os
import subprocess
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("ENV_PATH", "../../../envs/.env.test")
django.setup()

from django.db import connection
from django.test import TestCase
from web.models import IntegrationCredential


class EncryptionDependencyTests(TestCase):
    def test_imports_resolve_to_dependency_from_both_working_directories(self):
        project = Path(__file__).resolve().parents[3]
        repository = project.parent.parent
        code = (
            "from pathlib import Path; from importlib.metadata import distribution; "
            "import encrypted_fields; "
            "expected=distribution('django-fernet-encrypted-fields').locate_file('encrypted_fields/__init__.py'); "
            "assert Path(encrypted_fields.__file__).resolve()==Path(expected).resolve()"
        )
        for directory in (repository, project):
            with self.subTest(directory=directory):
                result = subprocess.run([sys.executable, "-c", code], cwd=directory, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_credentials_are_encrypted_at_rest_and_round_trip(self):
        credential = IntegrationCredential.objects.create(provider="cleanup-test", access_token="synthetic-test-token")
        with connection.cursor() as cursor:
            cursor.execute("SELECT access_token FROM web_integrationcredential WHERE id = %s", [credential.pk])
            stored = cursor.fetchone()[0]
        self.assertNotEqual(stored, "synthetic-test-token")
        self.assertNotIn("synthetic-test-token", stored)
        credential.refresh_from_db()
        self.assertEqual(credential.access_token, "synthetic-test-token")

    def test_legacy_plaintext_remains_readable_without_rewriting_existing_rows(self):
        credential = IntegrationCredential.objects.create(provider="cleanup-test")
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE web_integrationcredential SET access_token = %s WHERE id = %s",
                ["synthetic-legacy-token", credential.pk],
            )
        credential.refresh_from_db()
        self.assertEqual(credential.access_token, "synthetic-legacy-token")

from django.db import models


class EncryptedTextField(models.TextField):
    """
    Test-environment fallback when django-fernet-encrypted-fields is unavailable.

    This preserves the model field interface so imports, migrations, and CRUD tests
    can run in lightweight environments without the encryption dependency.
    """


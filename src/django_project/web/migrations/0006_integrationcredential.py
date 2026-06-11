import encrypted_fields.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0005_alter_event_location_fields_nullable"),
    ]

    operations = [
        migrations.CreateModel(
            name="IntegrationCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(max_length=64, unique=True)),
                ("access_token", encrypted_fields.fields.EncryptedTextField(blank=True, null=True)),
                ("refresh_token", encrypted_fields.fields.EncryptedTextField(blank=True, null=True)),
                ("access_token_expires_at", models.DateTimeField(blank=True, null=True)),
                ("refresh_token_expires_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["provider"]},
        ),
    ]

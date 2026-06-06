from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0004_alter_event_end_datetime"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="location_name",
            field=models.CharField(
                blank=True,
                help_text="name of location where this event is being hosted",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="location_address",
            field=models.CharField(
                blank=True,
                help_text="address of location where this event is being hosted",
                max_length=256,
                null=True,
            ),
        ),
    ]

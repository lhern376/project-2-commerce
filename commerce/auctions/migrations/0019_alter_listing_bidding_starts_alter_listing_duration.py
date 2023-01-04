# Generated by Django 4.1.3 on 2022-12-19 18:48

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0018_alter_listing_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="bidding_starts",
            field=models.DateTimeField(
                blank=True, default=django.utils.timezone.now, null=True
            ),
        ),
        migrations.AlterField(
            model_name="listing",
            name="duration",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(days=10, seconds=43200),
                help_text="Enter the duration of the listing",
                null=True,
            ),
        ),
    ]
# Generated by Django 4.1.3 on 2022-12-19 19:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0019_alter_listing_bidding_starts_alter_listing_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="duration",
            field=models.DurationField(
                blank=True,
                default=datetime.timedelta(0),
                help_text="Enter the duration of the listing",
                null=True,
            ),
        ),
    ]

# Generated by Django 4.1.3 on 2022-12-19 20:20

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0020_alter_listing_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="bidding_starts",
            field=models.DateTimeField(
                blank=True,
                default=datetime.datetime(2022, 12, 19, 15, 20, 39, 886841),
                null=True,
            ),
        ),
    ]

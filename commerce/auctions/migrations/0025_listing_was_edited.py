# Generated by Django 4.1.3 on 2022-12-30 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0024_comment_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="was_edited",
            field=models.BooleanField(default=False),
        ),
    ]

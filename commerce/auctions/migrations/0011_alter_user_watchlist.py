# Generated by Django 4.1.3 on 2022-12-06 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0010_user_watchlist_item_count_alter_user_watchlist"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="watchlist",
            field=models.ManyToManyField(
                blank=True, related_name="watchlist", to="auctions.listing"
            ),
        ),
    ]
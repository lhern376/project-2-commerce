# Generated by Django 4.1.3 on 2022-12-02 14:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("auctions", "0006_alter_category_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="listing",
            options={"ordering": ["status", "date_created"]},
        ),
    ]
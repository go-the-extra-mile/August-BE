# Generated by Django 4.2.3 on 2023-09-28 12:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_location_data_migration real'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='building',
        ),
    ]

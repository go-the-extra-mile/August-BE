# Generated by Django 4.2.3 on 2023-09-28 12:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_remove_location_building'),
    ]

    operations = [
        migrations.RenameField(
            model_name='location',
            old_name='building_obj',
            new_name='building',
        ),
    ]

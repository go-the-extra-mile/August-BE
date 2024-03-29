# Generated by Django 5.0.2 on 2024-02-29 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0022_remove_building_latitude_remove_building_longitude'),
        ('timetables', '0003_timetable_order_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='timetableopenedsection',
            constraint=models.UniqueConstraint(fields=('timetable', 'opened_section'), name='timetable consists of unique opened sections'),
        ),
    ]

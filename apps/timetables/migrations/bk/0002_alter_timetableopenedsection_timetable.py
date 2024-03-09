# Generated by Django 5.0.2 on 2024-02-29 09:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetables', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timetableopenedsection',
            name='timetable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opened_section_entries', to='timetables.timetable'),
        ),
    ]
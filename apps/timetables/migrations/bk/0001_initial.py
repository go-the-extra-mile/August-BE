# Generated by Django 5.0.2 on 2024-02-28 08:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0022_remove_building_latitude_remove_building_longitude'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.semester')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TimeTableOpenedSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opened_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.openedsection')),
                ('timetable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetables.timetable')),
            ],
        ),
    ]

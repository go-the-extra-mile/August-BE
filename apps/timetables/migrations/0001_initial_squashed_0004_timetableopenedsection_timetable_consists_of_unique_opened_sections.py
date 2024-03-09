# Generated by Django 5.0.2 on 2024-03-05 01:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('timetables', '0001_initial'), ('timetables', '0002_alter_timetableopenedsection_timetable'), ('timetables', '0003_timetable_order_and_more'), ('timetables', '0004_timetableopenedsection_timetable_consists_of_unique_opened_sections')]

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
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='TimeTableOpenedSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opened_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.openedsection')),
                ('timetable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opened_section_entries', to='timetables.timetable')),
            ],
        ),
        migrations.AddConstraint(
            model_name='timetable',
            constraint=models.UniqueConstraint(fields=('user', 'semester', 'order'), name='unique order for one user for one semester'),
        ),
        migrations.AddConstraint(
            model_name='timetableopenedsection',
            constraint=models.UniqueConstraint(fields=('timetable', 'opened_section'), name='timetable consists of unique opened sections'),
        ),
    ]
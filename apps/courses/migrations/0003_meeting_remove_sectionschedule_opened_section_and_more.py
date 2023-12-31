# Generated by Django 4.2.3 on 2023-08-02 10:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_credits'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.day')),
                ('duration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.duration')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.location')),
            ],
        ),
        migrations.RemoveField(
            model_name='sectionschedule',
            name='opened_section',
        ),
        migrations.RemoveField(
            model_name='sectionschedule',
            name='schedule',
        ),
        migrations.RemoveField(
            model_name='openedsection',
            name='location',
        ),
        migrations.DeleteModel(
            name='Schedule',
        ),
        migrations.DeleteModel(
            name='SectionSchedule',
        ),
        migrations.AddField(
            model_name='meeting',
            name='opened_section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.openedsection'),
        ),
    ]

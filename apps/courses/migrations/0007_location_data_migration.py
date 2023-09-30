from django.db import migrations

def migrate_building_data(apps, schema_editor):
    Location = apps.get_model('courses', 'Location')
    Building = apps.get_model('courses', 'Building')
    
    # We're assuming here that if two Locations have identical building names,
    # they are indeed referring to same physical building.
    
    for location in Location.objects.all():
        # Create or get existing Building object.
        building_obj, created = Building.objects.get_or_create(
            nickname=location.building,
            defaults={
                'full_name': '',  # Default values since we don't have these initially.
            }
        )
        
        location.building_obj = building_obj  # Assign new foreign key.
        location.save()

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_building_location_building_obj'),
    ]

    operations = [
        migrations.RunPython(code=migrate_building_data, reverse_code=migrations.RunPython.noop)
    ]

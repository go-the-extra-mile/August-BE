from rest_framework import serializers
from apps.courses.models import OpenedSection, Semester
from apps.courses.serializers import OpenedSectionSerializer
from apps.timetables.models import TimeTable, TimeTableOpenedSection


class TimeTableSerializer(serializers.ModelSerializer):
    sections = OpenedSectionSerializer(many=True, read_only=True, source='related_opened_sections')
    credits = serializers.IntegerField(read_only=True)
    section_ids = serializers.PrimaryKeyRelatedField(queryset=OpenedSection.objects.all(), write_only=True, many=True)

    class Meta:
        model = TimeTable
        fields = ["name", "credits", "sections", "section_ids", "order"]

    def create(self, validated_data):
        # Extract sections from validated_data
        sections = validated_data.pop('section_ids')

        # Check if the provided section ids are valid and belong to the same semester as the user provided
        opened_sections = OpenedSection.objects.filter(id__in=[section.id for section in sections])
        semester_code = self.context['request'].parser_context['kwargs']['semester']

        if not Semester.objects.filter(code=semester_code).exists():
            raise serializers.ValidationError({"error": "Semester does not exist"})

        # Get a list of semesters of the list of section ids using queryset api
        semesters = opened_sections.values_list('semester__code', flat=True)
        if len(set(semesters)) != 1 or semester_code not in semesters:
            raise serializers.ValidationError({"error": "Invalid section ids for semester"})

        # Create and save TimeTable instance
        timetable = TimeTable.objects.create(user=self.context['request'].user, semester=Semester.objects.get(code=semester_code), **validated_data)

        # Create and save TimeTableOpenedSection instances
        timetable_opened_sections = [
            TimeTableOpenedSection(timetable=timetable, opened_section=opened_section)
            for opened_section in opened_sections
        ]

        TimeTableOpenedSection.objects.bulk_create(timetable_opened_sections)

        return timetable
from rest_framework import serializers
from apps.courses.models import OpenedSection

from apps.courses.serializers import InstructorNameTeachSerializer, MeetingSerializer


class OpenedSectionWithCourseNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="section.course.name")
    credits = serializers.IntegerField(source="section.course.credits")
    section_code = serializers.CharField(source="section.section_code")
    instructors = InstructorNameTeachSerializer(source="teach_set", many=True)
    meetings = MeetingSerializer(source="meeting_set", many=True)

    class Meta:
        model = OpenedSection
        fields = (
            "id",
            "name",
            "credits",
            "section_code",
            "instructors",
            "meetings",
            "seats",
            "open_seats",
            "waitlist",
            "holdfile",
        )

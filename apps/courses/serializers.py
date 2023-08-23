from collections import defaultdict
from rest_framework import serializers
from apps.courses.models import (
    Instructor,
    Meeting, 
    OpenedSection,
    Teach, 
)

class MeetingSerializer(serializers.ModelSerializer):
    building = serializers.CharField(source='location.building')
    room = serializers.CharField(source='location.room')
    days = serializers.StringRelatedField(source='day.day')
    start_time = serializers.TimeField(format='%H:%M', source='duration.start_time')
    end_time = serializers.TimeField(format='%H:%M', source='duration.end_time')

    class Meta:
        model = Meeting
        fields = ('building', 'room', 'days', 'start_time', 'end_time')

class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ('name', )

    def to_representation(self, instance):
        return instance.name

class InstructorNameTeachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teach
        fields = []

    def to_representation(self, instance):
        return instance.instructor.name

class OpenedSectionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='section.course.name')
    
    course_code = serializers.CharField(source='section.course.course_code')
    section_code = serializers.CharField(source='section.section_code')
    credits = serializers.IntegerField(source='section.course.credits')

    meetings = MeetingSerializer(source='meeting_set', many=True)
    instructors = InstructorNameTeachSerializer(source='teach_set', many=True)

    class Meta:
        model = OpenedSection
        fields = ('id', 
                  'name', 
                  'course_code', 
                  'section_code', 
                  'instructors', 
                  'meetings', 
                  'credits',
                  )
        
class MergedMeetingsOpenedSectionSerializer(OpenedSectionSerializer):
    meetings = serializers.SerializerMethodField(method_name='get_meetings_with_merged_days')

    def get_meetings_with_merged_days(self, opened_section):
        meetings = opened_section.meeting_set.all() # a list of Meeting objects
        
        meeting_groups = defaultdict(list)
        for meeting in meetings:
            key = (meeting.duration_id, meeting.location_id)
            meeting_groups[key].append(meeting)
        
        merged_days = defaultdict(str)

        day_order = {"M": 0, "Tu": 1, "W": 2, "Th": 3, "F": 4, "Sa": 5, "Su": 6}
        ordering = lambda x: (day_order[x])
        for k, v in meeting_groups.items():
            days = [] # list of 'str' day
            for meeting in v:
                days.append(meeting.day.day)
            
            days = sorted(days, key=ordering)
            days_str = ''.join(d for d in days)
            merged_days[k] = days_str
        
        res = []
        for k, v in meeting_groups.items():
            meeting = v[0]
            serialized_meeting = MeetingSerializer(meeting).data
            serialized_meeting['days'] = merged_days[k]
            res.append(serialized_meeting)
        
        return res
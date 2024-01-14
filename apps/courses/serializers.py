from collections import defaultdict
from rest_framework import serializers
from apps.courses.models import (
    Course,
    Instructor,
    Meeting, 
    OpenedSection,
    Teach, 
)

class MeetingSerializer(serializers.ModelSerializer):
    building = serializers.CharField(source='location.building.nickname')
    room = serializers.CharField(source='location.room')
    days = serializers.StringRelatedField(source='day.day')
    start_time = serializers.TimeField(format='%H:%M', source='duration.start_time')
    end_time = serializers.TimeField(format='%H:%M', source='duration.end_time')

    class Meta:
        model = Meeting
        fields = ('building', 'room', 'days', 'start_time', 'end_time')

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
        fields = (
            'id', 
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

class BaseCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'name', 
            'course_code', 
            'credits', 
        )

class BaseInstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = (
            'name',
        )

class InstructorSectionSerializer(BaseInstructorSerializer):
    sections = serializers.SerializerMethodField()
    class Meta(BaseInstructorSerializer.Meta):
        fields = BaseInstructorSerializer.Meta.fields + (
            'sections',
        )
    
    def get_sections(self, instructor):
        instructor_sections = self.context.get('instructor_sections')
        if instructor_sections is None: return None

        return MergedMeetingsOpenedSectionSerializer(instructor_sections, many=True).data

class CourseSectionSerializer(BaseCourseSerializer):
    sections_by_instructor = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    
    class Meta(BaseCourseSerializer.Meta):
        fields = BaseCourseSerializer.Meta.fields + (
            'notes',
            'sections_by_instructor', 
        )

    def get_notes(self, course):
        notes = self.context.get('notes', None)
        if notes is None: return None

        return notes

    def get_sections_by_instructor(self, course):
        course_opened_sections = self.context.get('course_opened_sections', None)
        if course_opened_sections is None: return None

        # set of distinct instructors of course's opened sections
        teaches = Teach.objects.filter(opened_section__in=course_opened_sections)
        instructors = Instructor.objects.filter(teach__in=teaches).distinct()

        res = []
        for instructor in instructors:
            instructor_sections = course_opened_sections.filter(teach__instructor=instructor)

            res.append(InstructorSectionSerializer(instructor, context={'instructor_sections': instructor_sections}).data)
        
        return res
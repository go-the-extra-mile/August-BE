from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.courses.serializers import CourseSectionSerializer
from apps.courses.models import Course, Meeting, OpenedCourse, OpenedSection, Semester, Teach

# Create your views here.
class OpenedSectionListView(generics.ListAPIView):
    def get_queryset(self):
        semester_code = self.request.query_params.get('semester', None)
        query_type = self.request.query_params.get('querytype', None)
        query = self.request.query_params.get('query', None)

        if semester_code is None:
            raise ValidationError('Missing "semester" query parameter')
        if query_type is None:
            raise ValidationError('Missing "querytype" query parameter')
        if query is None:
            raise ValidationError('Missing "query" query parameter')
        
        queryset = OpenedSection.objects.filter(semester__code=semester_code).select_related('section__course')
        if query_type == 'code':
            if len(query) < 5: 
                raise ValidationError('Provide course code of at least 5 letters')
            queryset = queryset.filter(section__course__course_code__icontains=query)
        elif query_type == 'name':
            if len(query) < 5:
                raise ValidationError('Provide course name of at least 5 letters')
            queryset = queryset.filter(section__course__name__icontains=query)
        else:
            raise ValidationError('Invalid "querytype" query parameter. Acceptable values are "code", "name"')
        
        # prefetch related teach, instructors
        teach_set_prefetch = Prefetch(
            lookup='teach_set', 
            queryset=Teach.objects.select_related('instructor'),
        )
        queryset = queryset.prefetch_related(teach_set_prefetch)

        # prefetch related meetings, duration, location, and day
        meeting_set_prefetch = Prefetch(
            lookup='meeting_set', 
            queryset=Meeting.objects.select_related('duration', 'location', 'day'), 
        )
        queryset = queryset.prefetch_related(meeting_set_prefetch)

        # select related section, course
        queryset = queryset.select_related('section__course')

        return queryset
    
    def get(self, request, *args, **kwargs):
        try: 
            return self.list(request, *args, **kwargs)
        except ValidationError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()) # queryset of OpenedSection
        
        semester_code = self.request.query_params.get('semester')
        courses = Course.objects.filter(section__openedsection__in=queryset).distinct() # courses: distinct courses of queryset
        opened_courses = OpenedCourse.objects.filter(course__in=courses, semester__code=semester_code)
        
        res = []
        for o_c in opened_courses:
            course_opened_sections = queryset.filter(section__course=o_c.course)
            notes = o_c.notes
            res.append(CourseSectionSerializer(o_c.course, context={'course_opened_sections': course_opened_sections, 'notes': notes}).data)

        return Response(res)
    
class SemestersListView(generics.ListAPIView):
    queryset = Semester.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        semester_codes = list(queryset.values_list('code', flat=True))

        return Response(semester_codes)
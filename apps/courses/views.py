from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.courses.serializers import MergedMeetingsOpenedSectionSerializer
from apps.courses.models import Meeting, OpenedSection, Teach

# Create your views here.
class OpenedSectionListView(generics.ListAPIView):
    serializer_class = MergedMeetingsOpenedSectionSerializer

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
            if len(query) < 4: 
                raise ValidationError('Provide course code of at least 4 letters')
            queryset = queryset.filter(section__course__course_code__icontains=query)
        elif query_type == 'name':
            if len(query) < 4:
                raise ValidationError('Provide course name of at least 4 letters')
            queryset = queryset.filter(section__course__name__icontains=query)
        else:
            raise ValidationError('Invalid "querytype" query parameter. Acceptable values are "code", "name"')
        
        # prefetch teach_set and instructors as teachs_cached
        teach_set_prefetch = Prefetch(
            lookup='teach_set', 
            queryset=Teach.objects.select_related('instructor'),
        )
        queryset = queryset.prefetch_related(teach_set_prefetch)

        # prefetch meetings and duration, location, day as meetings_cached
        meeting_set_prefetch = Prefetch(
            lookup='meeting_set', 
            queryset=Meeting.objects.select_related('duration', 'location', 'day'), 
        )
        queryset = queryset.prefetch_related(meeting_set_prefetch)

        print(f'ran')
        return queryset
    
    def get(self, request, *args, **kwargs):
        try: 
            return super().get(request, *args, **kwargs)
        except ValidationError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
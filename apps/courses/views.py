from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from rest_framework import generics, status
from rest_framework.response import Response

from apps.courses.serializers import (
    CourseSectionByInstructorSerializer,
    CourseSectionSerializer,
    DepartmentSerializer,
    InstitutionSerializer,
)
from apps.courses.models import (
    Course,
    Department,
    Institution,
    Meeting,
    OpenedCourse,
    OpenedSection,
    Semester,
    Teach,
)


class OpenedSectionListView(generics.ListAPIView):
    def get_queryset(self):
        semester_code = self.request.query_params.get("semester", None)
        query_type = self.request.query_params.get("querytype", None)
        query = self.request.query_params.get("query", None)
        institution_id = self.request.query_params.get("institution_id", 1)

        if semester_code is None:
            raise ValidationError('Missing "semester" query parameter')
        if query_type is None:
            raise ValidationError('Missing "querytype" query parameter')
        if query is None:
            raise ValidationError('Missing "query" query parameter')

        queryset = OpenedSection.objects.filter(
            semester__code=semester_code, section__course__institution_id=institution_id
        ).select_related("section__course")
        if query_type == "code":
            if len(query) < 4:
                raise ValidationError("Provide course code of at least 4 letters")
            queryset = queryset.filter(section__course__course_code__icontains=query)
        elif query_type == "name":
            if len(query) < 4:
                raise ValidationError("Provide course name of at least 4 letters")
            queryset = queryset.filter(section__course__name__icontains=query)
        else:
            raise ValidationError(
                'Invalid "querytype" query parameter. Acceptable values are "code", "name"'
            )

        # prefetch related teach, instructors
        teach_set_prefetch = Prefetch(
            lookup="teach_set",
            queryset=Teach.objects.select_related("instructor"),
        )
        queryset = queryset.prefetch_related(teach_set_prefetch)

        meeting_set_prefetch = Prefetch(
            lookup="meeting_set",
            queryset=Meeting.objects.select_related(
                "duration", "day", "location__building"
            ),
        )
        queryset = queryset.prefetch_related(meeting_set_prefetch)

        return queryset

    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except ValidationError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        opened_section_non_prefetched = queryset.prefetch_related(None)
        courses = Course.objects.filter(
            section__openedsection__in=opened_section_non_prefetched
        )  # courses: corresponding courses of queryset(opened sections)
        semester = Semester.objects.get(code=request.query_params.get("semester"))
        opened_courses = OpenedCourse.objects.filter(
            course__in=courses, semester=semester
        ).select_related("course")

        course_sections = []
        for o_c in opened_courses:
            course_sections.append(
                CourseSectionSerializer(
                    o_c.course,
                    context={
                        "course_opened_sections": queryset.filter(
                            section__course_id=o_c.course_id
                        ),
                        "notes": o_c.notes,
                    },
                ).data
            )

        return Response(course_sections)


# Create your views here.
class OpenedSectionByCourseByInstructorListView(generics.ListAPIView):
    def get_queryset(self):
        semester_code = self.request.query_params.get("semester", None)
        query_type = self.request.query_params.get("querytype", None)
        query = self.request.query_params.get("query", None)
        institution_id = self.request.query_params.get("institution_id", 1)

        if semester_code is None:
            raise ValidationError('Missing "semester" query parameter')
        if query_type is None:
            raise ValidationError('Missing "querytype" query parameter')
        if query is None:
            raise ValidationError('Missing "query" query parameter')

        queryset = OpenedSection.objects.filter(
            semester__code=semester_code, section__course__institution_id=institution_id
        ).select_related("section__course")
        if query_type == "code":
            if len(query) < 4:
                raise ValidationError("Provide course code of at least 4 letters")
            queryset = queryset.filter(section__course__course_code__icontains=query)
        elif query_type == "name":
            if len(query) < 4:
                raise ValidationError("Provide course name of at least 4 letters")
            queryset = queryset.filter(section__course__name__icontains=query)
        else:
            raise ValidationError(
                'Invalid "querytype" query parameter. Acceptable values are "code", "name"'
            )

        # prefetch related teach, instructors
        teach_set_prefetch = Prefetch(
            lookup="teach_set",
            queryset=Teach.objects.select_related("instructor"),
        )
        queryset = queryset.prefetch_related(teach_set_prefetch)

        # select related section for section_code retreival
        queryset.select_related("section")

        return queryset

    def get(self, request, *args, **kwargs):
        try:
            return self.list(request, *args, **kwargs)
        except ValidationError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # queryset of OpenedSection

        opened_section_non_prefetched = queryset.prefetch_related(None)
        courses = Course.objects.filter(
            section__openedsection__in=opened_section_non_prefetched
        )  # courses: corresponding courses of queryset(opened sections)
        semester = Semester.objects.get(code=request.query_params.get("semester"))
        opened_courses = OpenedCourse.objects.filter(
            course__in=courses, semester=semester
        ).select_related("course")
        # opened_courses: corresponding opened_courses of queryset(opened sections)

        res = []
        for o_c in opened_courses:
            res.append(
                CourseSectionByInstructorSerializer(
                    o_c.course,
                    context={
                        "course_opened_sections": queryset.filter(
                            section__course_id=o_c.course_id
                        ),
                        "notes": o_c.notes,
                    },
                ).data
            )

        return Response(res)


class SemestersListView(generics.ListAPIView):
    queryset = Semester.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        semester_codes = list(queryset.values_list("code", flat=True))

        return Response(semester_codes)


class InstitutionListView(generics.ListAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer


class DepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        institution_id = self.request.query_params.get("institution_id", 1)

        return super().get_queryset().filter(institution_id=institution_id)

from django.db import IntegrityError
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
)
from rest_framework.response import Response
from rest_framework import status

from apps.courses.models import OpenedSection, Semester
from apps.timetables.models import TimeTable, TimeTableOpenedSection
from apps.timetables.serializers import TimeTableSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


class TimeTableListView(ListCreateAPIView):
    serializer_class = TimeTableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        semester_code = self.kwargs["semester"]
        try:
            semester = Semester.objects.get(code=semester_code)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        return TimeTable.objects.filter(
            user=self.request.user, semester=semester
        ).order_by("order")


class TimeTableView(RetrieveUpdateDestroyAPIView):
    queryset = TimeTable.objects.all()
    serializer_class = TimeTableSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset,
            user=self.request.user,
            semester=Semester.objects.get(code=self.kwargs["semester"]),
            order=self.kwargs["order"],
        )
        return obj


class TimeTableSectionAddView(CreateAPIView):
    queryset = TimeTableOpenedSection.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            timetable = TimeTable.objects.get(
                user=request.user,
                semester=Semester.objects.get(code=self.kwargs["semester"]),
                order=self.kwargs["order"],
            )
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "TimeTable does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            opened_section_id = int(request.data)
            opened_section = OpenedSection.objects.get(id=opened_section_id)
        except OpenedSection.DoesNotExist:
            return Response(
                {"error": "Section with given ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if the opened section's semester is identical to the timetable's semester
        if opened_section.semester.code != timetable.semester.code:
            return Response(
                {"error": "Section's semester and timetable's semester mismatch"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a TimeTableOpenedSection instance
        try:
            TimeTableOpenedSection.objects.create(
                timetable=timetable, opened_section=opened_section
            )
        except IntegrityError:
            return Response(
                {"error": "Section already exists in timetable"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Successfully added section to timetable"},
            status=status.HTTP_201_CREATED,
        )

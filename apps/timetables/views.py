from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    DestroyAPIView,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

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

    def perform_destroy(self, instance):
        instance.delete()

        # get the remaining timetables for the same semester and user, with order greater than the deleted timetable's order
        remaining_timetables = TimeTable.objects.filter(
            user=instance.user, semester=instance.semester, order__gt=instance.order
        )

        # decrement the order of the remaining timetables, and update as bulk
        remaining_timetables.update(order=F("order") - 1)


class TimeTableSectionAddView(CreateAPIView):
    queryset = TimeTableOpenedSection.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            timetable = TimeTable.objects.get(
                user=request.user,
                semester__code=self.kwargs["semester"],
                order=self.kwargs["order"],
            )
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "TimeTable does not exist"}, status=status.HTTP_404_NOT_FOUND
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
            status=status.HTTP_201_CREATED,
        )


class TimeTableSectionDeleteView(DestroyAPIView):
    queryset = TimeTableOpenedSection.objects.all()
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        section_id = self.kwargs["section_id"]

        try:
            timetable = TimeTable.objects.get(
                user=request.user,
                semester__code=self.kwargs["semester"],
                order=self.kwargs["order"],
            )
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "Timetable does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get the timetable opened section for the given section_id
        try:
            timetable_opened_section = TimeTableOpenedSection.objects.get(
                timetable=timetable, opened_section__id=section_id
            )
        except TimeTableOpenedSection.DoesNotExist:
            return Response(
                {"error": "Section not in timetable"}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete the TimeTableOpenedSection instance
        timetable_opened_section.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class TimeTableReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Extract semester from the URL parameters
        semester_code = self.kwargs["semester"]

        new_order = request.data

        # Get the timetables to be reordered
        timetables = TimeTable.objects.filter(
            user=request.user, semester__code=semester_code
        ).order_by("order")

        # Validate the new order
        if set(new_order) != set(range(timetables.count())):
            return Response(
                {"error": "Invalid order"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mapping of old order and new order
        order_mapping = {old_order: new_order for old_order, new_order in enumerate(new_order)}

        # Temporarily update the orders to (maximum order value) + 1 + (new order value)
        with transaction.atomic():
            for timetable in timetables:
                timetable.order = len(new_order) + order_mapping[timetable.order]
                timetable.save()

        # Update the order of the timetables with the new order
        with transaction.atomic():
            for timetable in timetables:
                timetable.order = F("order") - len(new_order)
                timetable.save()

        return Response(status=status.HTTP_200_OK)


from datetime import datetime, timedelta
from geopy.distance import distance

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Prefetch
from django.core.exceptions import ValidationError

from apps.courses.models import Meeting, OpenedSection, Teach
from apps.wizard.serializers import WizardOpenedSectionSerializer

import json
import time

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed

class GenerateTimeTableMixin:
    groups = None
    generated_time_tables = None
    minimum_interval = None
    maximum_interval = None
    maximum_consecutive_classes = None

    @timeit
    def exclude_early_classes(self, min_start_time):
        res = []
        for sections in self.groups:
            late_sections = sections.exclude(
                meeting__duration__start_time__lt=min_start_time
            )

            res.append(late_sections)

        self.groups = res

    @timeit
    def _too_short_interval(self, meetings1, meetings2):
        if self.minimum_interval is None:
            return False

        for m1 in meetings1:
            for m2 in meetings2:
                if m1.day.day != m2.day.day:
                    continue

                before = m1 if m1.duration.start_time <= m2.duration.start_time else m2
                after = m2 if before == m1 else m1

                # interval = (start time of after) - (end time of before)
                today = datetime.today().date()
                interval = datetime.combine(
                    today, after.duration.start_time
                ) - datetime.combine(today, before.duration.end_time)

                if interval < self.minimum_interval:
                    return True

        return False

    @timeit
    def _too_long_interval(self, meetings1, meetings2):
        if self.maximum_interval is None:
            return False

        for m1 in meetings1:
            for m2 in meetings2:
                before = m1 if m1.duration.start_time <= m2.duration.start_time else m2
                after = m2 if before == m1 else m1

                # interval = (start time of after) - (end time of before)
                today = datetime.today().date()
                interval = datetime.combine(
                    today, after.duration.start_time
                ) - datetime.combine(today, before.duration.end_time)

                if interval > self.maximum_interval:
                    return True

        return False

    @timeit
    def _too_many_consec_classes(self, meetings1, meetings2):
        if self.maximum_consecutive_classes is None:
            return False

        meetings = meetings1 | meetings2  # all meetings

        days_in_meetings = meetings.values_list("day", flat=True).distinct()

        for day in days_in_meetings:
            consec_cnt = 1
            day_meetings = meetings.filter(day=day).order_by("duration__start_time")
            for i in range(0, len(day_meetings) - 1):
                before = day_meetings[i]
                after = day_meetings[i + 1]

                # interval = (start time of after) - (end time of before)
                today = datetime.today().date()
                interval = datetime.combine(
                    today, after.duration.start_time
                ) - datetime.combine(today, before.duration.end_time)

                if interval <= timedelta(minutes=15):
                    consec_cnt += 1
                    if consec_cnt > self.maximum_consecutive_classes:
                        return True
                else:
                    consec_cnt = 1

        return False

    @timeit
    def exclude_one_class_a_day_tables(self):
        res = []

        for table in self.generated_time_tables:
            courses_a_day = {}
            for section in table:
                days = Meeting.objects.filter(opened_section=section).values_list(
                    "day__day", flat=True
                )
                for day in days:
                    courses_a_day[day] = courses_a_day.get(day, 0) + 1

            include_table = True
            for day in courses_a_day:
                if courses_a_day[day] == 1:
                    include_table = False
                    break

            if include_table:
                res.append(table)

        self.generated_time_tables = res

    @timeit
    def _overlap(self, meetings_1, meetings_2):
        for m1 in meetings_1:
            for m2 in meetings_2:
                if m1.day.day != m2.day.day:
                    continue

                if not (
                    m1.duration.end_time <= m2.duration.start_time
                    or m2.duration.end_time <= m1.duration.start_time
                ):
                    return True
        return False

    @timeit
    def _insertable(self, section, table):
        if section in table:
            return False

        meetings = section.meeting_set.all()

        all_existing_meetings = Meeting.objects.none()
        for existing_section in table:
            existing_meetings = existing_section.meeting_set.all()
            all_existing_meetings |= existing_meetings

            if self._overlap(meetings, existing_meetings):
                return False
            if self._too_short_interval(meetings, existing_meetings):
                return False
            if self._too_long_interval(meetings, existing_meetings):
                return False

        if self._too_many_consec_classes(meetings, all_existing_meetings):
            return False

        return True

    @timeit
    def _generate_time_tables(self, cur, table):
        if cur >= len(self.groups):
            self.generated_time_tables.append(set(table))
            return

        for section in self.groups[cur]:
            if self._insertable(section, table):
                table.add(section)
                self._generate_time_tables(cur + 1, table)
                table.remove(section)

    def generate_time_tables(self):
        self.generated_time_tables = []
        self._generate_time_tables(0, set())
        return self.generated_time_tables

    def to_opened_sections_groups(self, opened_section_id_groups):
        # turn a list of section ids 'opened_section_id_groups' into a list of QuerySets of the corresponding section ids w/ prefetch & select
        groups = []
        for group in opened_section_id_groups:
            queryset = OpenedSection.objects.filter(id__in=group)
            queryset = queryset.prefetch_related(
                Prefetch(
                    lookup="meeting_set",
                    queryset=Meeting.objects.select_related(
                        "duration", "day", "location", "location__building"
                    ),
                ),
                Prefetch(
                    lookup="teach_set",
                    queryset=Teach.objects.select_related("instructor"),
                ),
            )
            queryset = queryset.select_related("section__course")
            groups.append(queryset)

        return groups
    
    def exclude_not_opened_sections(self):
        res = []
        for group in self.groups:
            opened_sections = group.filter(open_seats__gt=0)
            res.append(opened_sections)

        self.groups = res

    def generate_with_options(self, opened_section_id_groups, options):
        if not isinstance(opened_section_id_groups, list) and all(
            isinstance(i, int) for i in opened_section_id_groups
        ):
            return
        self.groups = self.to_opened_sections_groups(opened_section_id_groups)

        opened_sections_only = options.get("allow_only_open_section", False)
        if opened_sections_only:
            self.exclude_not_opened_sections()

        minimum_start_time = options.get("minimum_start_time", None)
        if minimum_start_time is not None:
            try:
                minimum_start_time = datetime.strptime(
                    minimum_start_time, "%H:%M"
                ).time()
                self.exclude_early_classes(minimum_start_time)
            except ValueError as e:
                print(f"Wrong value given for minimum_start_time: {minimum_start_time}")
                print(e)

        min_interval = options.get("minimum_interval", None)
        if min_interval is not None:
            try:
                self.minimum_interval = datetime.strptime(min_interval, "%H:%M").time()
                self.minimum_interval = timedelta(
                    hours=self.minimum_interval.hour,
                    minutes=self.minimum_interval.minute,
                )
            except ValueError as e:
                print(f"Wrong value given for minimum_interval: {minimum_start_time}")
                print(e)

        max_interval = options.get("maximum_interval", None)
        if max_interval is not None:
            try:
                self.maximum_interval = datetime.strptime(max_interval, "%H:%M").time()
                self.maximum_interval = timedelta(
                    hours=self.maximum_interval.hour,
                    minutes=self.maximum_interval.minute,
                )
            except ValueError as e:
                print(f"Wrong value given for maximum_interval: {max_interval}")
                print(e)

        consec_classes = options.get("allow_consec", None)
        if consec_classes is not None:
            try:
                self.maximum_consecutive_classes = (
                    int(consec_classes) if int(consec_classes) >= 1 else None
                )
            except ValueError as e:
                print(f"Wrong value given for allow_consec: {consec_classes}")
                print(e)

        self.generate_time_tables()

        allow_one_class_a_day = options.get("allow_one_class_a_day", None)
        if allow_one_class_a_day is not None:
            try:
                allow_one_class_a_day = bool(allow_one_class_a_day)
                if allow_one_class_a_day is not True:
                    self.exclude_one_class_a_day_tables()
            except ValueError as e:
                print(
                    f"Wrong value given for allow_one_class_a_day: {allow_one_class_a_day}"
                )
                print(e)


class GeneratedTimeTableView(GenerateTimeTableMixin, APIView):
    def get(self, request, format=None):
        opened_section_id_groups = request.data.get("groups", None)
        options = request.data.get("options", None)

        try:
            if opened_section_id_groups is None:
                raise ValidationError("groups are required")
            if options is None:
                raise ValidationError("options are required")
        except ValidationError as e:
            return Response(data=str(e), status=status.HTTP_400_BAD_REQUEST)

        self.generate_with_options(opened_section_id_groups, options)

        res = []
        try:
            for table in self.generated_time_tables:
                res.append(WizardOpenedSectionSerializer(table, many=True).data)
        except TypeError as e:
            print(f"No generated time tables")
            print(e)

        return Response(res)

    def post(self, request, format=None):
        return self.get(request, format)


class GeneratedTimeTableCountView(GenerateTimeTableMixin, APIView):
    def get(self, request, format=None):
        opened_section_id_groups = request.data.get("groups", None)
        options = request.data.get("options", None)

        try:
            if opened_section_id_groups is None:
                raise ValidationError("groups are required")
            if options is None:
                raise ValidationError("options are required")
        except ValidationError as e:
            return Response(data=str(e), status=status.HTTP_400_BAD_REQUEST)

        self.generate_with_options(opened_section_id_groups, options)

        try:
            return Response(len(self.generated_time_tables))
        except TypeError as e:
            print("No generated time tables")
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        return self.get(request, format)


class GeneratedTimeTableTestView(APIView):
    test_request = None
    
    def __init__(self):
        super().__init__()
        with open('test/request.json') as f:
            self.test_request = json.load(f)

    def get(self, request):
        for key, val in self.test_request.items():
            request.data[key] = val

        test_view = GeneratedTimeTableView()
        return test_view.get(request)

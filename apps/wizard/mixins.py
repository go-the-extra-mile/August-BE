from datetime import datetime, timedelta
from functools import reduce

from django.db.models import Prefetch, Exists, OuterRef

from apps.courses.models import Meeting, OpenedSection, Teach


def raise_(ex):
    raise ex


class GenerateTimeTableMixin:
    _opened_section_id_groups = None
    _groups: (
        list[dict[tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]]]
        | None
    ) = None
    _options = None
    generated_timetables: list[
        dict[tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]]
    ] = None
    realized_timetables: list[list[OpenedSection]] = None
    OPTIONS_SPEC = {
        "minimum_start_time": lambda x: datetime.strptime(x, "%H:%M").time(),
        "minimum_interval": lambda x: datetime.combine(
            datetime.min, datetime.strptime(x, "%H:%M").time()
        )
        - datetime.min,
        "maximum_interval": lambda x: datetime.combine(
            datetime.min, datetime.strptime(x, "%H:%M").time()
        )
        - datetime.min,
        "allow_consec": lambda x: (
            int(x)
            if int(x) >= 1
            else raise_(ValueError("Invalid value for option 'allow_consec'"))
        ),
        "allow_one_class_a_day": lambda x: bool(x),
        "allow_only_open_section": lambda x: bool(x),
    }

    def _generate_timetables(
        self,
        gr_num: int,
        timetable: dict[
            tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]
        ],
    ):
        """
        Generate timetables with self._groups and self._options

        :param gr_idx: The index of the group to be processed
        :param timetable: A dictionary that maps timeslots to OpenedSection objects
        """

        if gr_num == len(self._groups):
            self.generated_timetables.append(timetable)
            return

        for timeslots in self._groups[gr_num].keys():
            if self.insertable(timeslots, timetable):
                new_timetable = timetable.copy()
                new_timetable[timeslots] = self._groups[gr_num][timeslots]
                self._generate_timetables(gr_num + 1, new_timetable)

    def insertable(
        self,
        timeslots: tuple,
        timetable: dict[
            tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]
        ],
    ):
        """
        Returns True if the timeslots can be inserted into the timetable without conflicts and satisfies the options.

        :param timeslots: A tuple of timeslots
        :param timetable: A dictionary that maps timeslots to OpenedSection objects
        """

        if timeslots in timetable:
            return False

        for table_timeslots in timetable:
            if any(
                [
                    self._overlap(timeslots, table_timeslots),
                    self._too_short_interval(timeslots, table_timeslots),
                    self._too_long_interval(timeslots, table_timeslots),
                ]
            ):
                return False

        if self._too_many_consec_classes(timeslots, timetable.keys()):
            return False

        return True

    def _overlap(
        self,
        timeslots1: tuple[tuple[str, datetime.time, datetime.time]],
        timeslots2: tuple[tuple[str, datetime.time, datetime.time]],
    ):
        """
        Returns True if the two timeslots overlap.

        :param timeslots1: A tuple of timeslots
        :param timeslots2: A tuple of timeslots
        """

        for day1, start1, end1 in timeslots1:
            for day2, start2, end2 in timeslots2:
                if day1 != day2:
                    continue
                if start1 < end2 and start2 < end1:
                    return True

        return False

    def _too_short_interval(
        self,
        timeslots1: tuple[tuple[str, datetime.time, datetime.time]],
        timeslots2: tuple[tuple[str, datetime.time, datetime.time]],
    ):
        """
        Returns True if the interval between the two timeslots is too short.

        :param timeslots1: A tuple of timeslots
        :param timeslots2: A tuple of timeslots
        """

        min_interval = self._options["minimum_interval"]
        if min_interval is None:
            return False

        for ts1 in timeslots1:
            for ts2 in timeslots2:
                day1, start1, _ = ts1
                day2, start2, _ = ts2

                if day1 != day2:
                    continue

                before = ts1 if start1 < start2 else ts2
                after = ts1 if before == ts2 else ts2

                # interval := start time of after - end time of before
                interval = datetime.combine(
                    datetime.today(), after[1]
                ) - datetime.combine(datetime.today(), before[2])
                if interval < min_interval:
                    return True

        return False

    def _too_long_interval(
        self,
        timeslots1: tuple[tuple[str, datetime.time, datetime.time]],
        timeslots2: tuple[tuple[str, datetime.time, datetime.time]],
    ):
        """
        Returns True if the interval between the two timeslots is too long.

        :param timeslots1: A tuple of timeslots
        :param timeslots2: A tuple of timeslots
        """

        max_interval = self._options["maximum_interval"]
        if max_interval is None:
            return False

        for ts1 in timeslots1:
            for ts2 in timeslots2:
                day1, start1, _ = ts1
                day2, start2, _ = ts2

                if day1 != day2:
                    continue

                before = ts1 if start1 < start2 else ts2
                after = ts1 if before == ts2 else ts2

                # interval := start time of after - end time of before
                interval = datetime.combine(
                    datetime.today(), after[1]
                ) - datetime.combine(datetime.today(), before[2])
                if interval > max_interval:
                    return True

        return False

    def _too_many_consec_classes(
        self,
        timeslots: tuple[tuple[str, datetime.time, datetime.time]],
        timetable: list[tuple[tuple[str, datetime.time, datetime.time]]],
    ):
        """
        Returns True if the number of consecutive classes is too many.

        :param timeslots: A tuple of timeslots
        :param timetable: A list of timeslots
        """
        # days in timeslots := unique days in `timeslots`
        days_in_timeslots = set([ts[0] for ts in timeslots])

        # flatten timetable timeslot sets to a list s.t. it only has the days in `days_in_timeslots`
        all_timeslots = [
            ts for ts_set in timetable for ts in ts_set if ts[0] in days_in_timeslots
        ]

        # append all elements of `timeslots` to `all_timeslots`
        all_timeslots.extend(timeslots)

        # split timetable_timeslots by day
        all_timeslots_by_day: dict[
            str, list[tuple[str, datetime.time, datetime.time]]
        ] = {}
        for ts in all_timeslots:
            day, _, _ = ts
            if day not in all_timeslots_by_day:
                all_timeslots_by_day[day] = []
            all_timeslots_by_day[day].append(ts)

        # check if there are too many consecutive classes
        allowed_consec_classes = self._options["allow_consec"]
        for day in days_in_timeslots:
            # sort a day's timeslots by start time
            day_timeslots = sorted(all_timeslots_by_day[day], key=lambda x: x[1])

            # count the number of consecutive classes
            consec_classes = 1
            for i in range(len(day_timeslots) - 1):
                _, _, end1 = day_timeslots[i]
                _, start2, _ = day_timeslots[i + 1]

                # let consecutive classes be classes with leq 15 minute gap
                # turn time into datetime object to compare
                start2 = datetime.combine(datetime.min, start2)
                end1 = datetime.combine(datetime.min, end1)

                if start2 - end1 <= timedelta(minutes=15):
                    consec_classes += 1
                    if consec_classes > allowed_consec_classes:
                        return True
                else:
                    consec_classes = 1

        return False

    def generate_timetables(self):
        """
        Generate timetables with self._groups and self._options
        """

        if self._groups is None or self._options is None:
            return

        self.generated_timetables = []
        self._generate_timetables(0, dict())

    def exclude_not_opened_sections(self):
        """
        Exclude all opened sections that are not open.
        """

        if self._groups is None:
            return None

        updated_groups = []
        for group in self._groups:
            updated_group: dict[
                tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]
            ] = {}
            for timeslots, op_secs in group.items():
                for op_sec in op_secs:
                    if op_sec.open_seats > 0:
                        if timeslots not in updated_group:
                            updated_group[timeslots] = []
                        updated_group[timeslots].append(op_sec)

            updated_groups.append(updated_group)

        self._groups = updated_groups

    def get_timetables_count(self, opened_section_id_groups, options):
        """
        Given a list of OpenedSection queryset objects(group), and a dictionary of options, return the number of possible timetables.

        :param opened_section_id_groups: A list of OpenedSection queryset objects' ids
        :param options: A dictionary of options
        """
        self.validate_opened_section_id_groups(opened_section_id_groups)
        self.validate_options(options)
        self._groups = self.to_timeslot_groups(self._opened_section_id_groups)

        if self._options["allow_only_open_section"] is True:
            self.exclude_not_opened_sections()
        if self._options["minimum_start_time"] is not None:
            self.exclude_early_classes()

        self.generate_timetables()

        # the number of possible timetables := sum(product(len(op_secs) for timetable in generated_timetables for op_secs in timetable.values()))
        return sum(
            reduce(
                lambda x, y: x * y, [len(op_secs) for op_secs in timetable.values()], 1
            )
            for timetable in self.generated_timetables
        )

    def get_timetables(self, opened_section_id_groups, options):
        """
        Given a list of OpenedSection queryset objects(group), and a dictionary of options, return a list of possible timetables.

        :param opened_section_id_groups: A list of OpenedSection queryset objects' ids
        :param options: A dictionary of options
        """
        self.validate_opened_section_id_groups(opened_section_id_groups)
        self.validate_options(options)
        self._groups = self.to_timeslot_groups(self._opened_section_id_groups)

        if self._options["allow_only_open_section"] is True:
            self.exclude_not_opened_sections()
        if self._options["minimum_start_time"] is not None:
            self.exclude_early_classes()

        self.generate_timetables()
        self.realize_timetables()

        return self.realized_timetables

    def realize_timetables(self):
        """
        Realize the timetables by picking one OpenedSection from each generated timetables to form a list of timetables that are a list of OpenedSection objects.
        """

        if self.generated_timetables is None:
            return

        self.realized_timetables = []
        for timetable_idx in range(len(self.generated_timetables)):
            self._realize_timetables(timetable_idx, 0, [])

    def _realize_timetables(
        self, timetable_idx: int, gr_idx: int, realization: list[OpenedSection]
    ):
        """
        Realize the timetables by picking one OpenedSection from each generated timetables to form a list of timetables that are a list of OpenedSection objects.

        :param timetable_idx: The index of the timetable to be processed
        :param gr_idx: The index of the group to be processed
        :param timetable: A list of OpenedSection objects
        """
        if gr_idx == len(self.generated_timetables[timetable_idx]):
            self.realized_timetables.append(realization)
            return

        timetable = self.generated_timetables[timetable_idx]
        key = list(timetable.keys())[gr_idx]
        op_secs = timetable[key]
        for op_sec in op_secs:
            new_realization = realization.copy()
            new_realization.append(op_sec)
            self._realize_timetables(timetable_idx, gr_idx + 1, new_realization)

    def exclude_not_opened_sections(self):
        """
        Exclude all opened sections that do not have seats available.
        """

        if self._groups is None:
            return None

        updated_groups = {}
        for timeslots, op_secs in self._groups.items():
            updated_groups[timeslots] = [
                op_sec
                for op_sec in op_secs
                if (op_sec is not None and op_sec.open_seats > 0)
            ]

        self._groups = updated_groups

    def exclude_early_classes(self):
        """
        Exclude all opened sections that start before min_start_time.

        :param min_start_time: A datetime.time object
        """

        if self._groups is None:
            return None

        min_start_time = self._options["minimum_start_time"]
        updated_groups = []
        for group in self._groups:
            updated_group: dict[
                tuple[tuple[str, datetime.time, datetime.time]], list[OpenedSection]
            ] = {}
            for timeslots in group:
                for _, start_time, _ in timeslots:
                    if start_time >= min_start_time:  # not early class
                        updated_group[timeslots] = group[timeslots]
            updated_groups.append(updated_group)

        self._groups = updated_groups

    def validate_opened_section_id_groups(self, opened_section_id_groups):
        """
        Given a list of OpenedSection queryset objects(group), validate if the groups are valid.

        :param opened_section_id_groups: A list of OpenedSection queryset objects' ids
        """

        if not all(isinstance(group, list) for group in opened_section_id_groups):
            raise ValueError("Invalid groups")

        for group in opened_section_id_groups:
            if not all(isinstance(id_, int) for id_ in group):
                raise ValueError("Invalid section ID")

        self._opened_section_id_groups = opened_section_id_groups

    def validate_options(self, options: dict):
        """
        Given a dictionary of options, validate if the options are valid.

        :param options: A dictionary of options
        """
        validated_options = {}

        for opt, validate in self.OPTIONS_SPEC.items():
            if opt not in options:
                raise ValueError(f"Missing option '{opt}'")

            try:
                validated_options[opt] = validate(options[opt])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for option '{opt}'")

        self._options = validated_options

    def to_timeslot_groups(self, opened_section_id_groups: list[list[int]]):
        """
        Given a list of OpenedSection queryset objects(group), convert to a dict that maps timeslots to OpenedSection objects.
        Cache the results in self._groups

        :param opened_section_id_groups: A list of OpenedSection queryset objects' ids
        """

        # convert to a dict that maps timeslots to OpenedSection objects
        groups = []
        for opened_section_id_group in opened_section_id_groups:
            group: dict[tuple, list[OpenedSection]] = {}
            queryset = OpenedSection.objects.filter(id__in=opened_section_id_group)

            # prefetch related fields required in response
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

            # filter out sections that have no meetings
            queryset = queryset.annotate(
                has_meetings=Exists(
                    Meeting.objects.filter(opened_section=OuterRef("pk"))
                )
            ).filter(has_meetings=True)

            for op_sec in queryset:
                timeslots = (
                    Meeting.objects.filter(opened_section=op_sec)
                    .values_list(
                        "day__day", "duration__start_time", "duration__end_time"
                    )
                    .distinct()
                )
                timeslots = tuple(sorted(list(timeslots)))

                if timeslots not in group:
                    group[timeslots] = []
                group[timeslots].append(op_sec)
            groups.append(group)

        return groups

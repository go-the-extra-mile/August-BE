from django.db import models
from django.conf import settings
from django.db.models import Sum, F

from apps.courses.models import OpenedSection


class TimeTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    semester = models.ForeignKey("courses.Semester", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.name}'s {self.semester} TimeTable"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "semester", "order"], name="unique order for one user for one semester")
        ]

    @property
    def credits(self):
        # get the sum of credits from opened_sections
        return TimeTableOpenedSection.objects.filter(timetable=self).aggregate(
            total_credits=Sum("opened_section__section__course__credits")
        )["total_credits"]

    @property
    def related_opened_sections(self):
        opened_sections = OpenedSection.objects.filter(
            timetableopenedsection__timetable=self
        )
        # annotate with course credits
        opened_sections = opened_sections.annotate(
            credits=F("section__course__credits")
        )
        return opened_sections

    def get_order(self):
        # get the last order of the user's timetable
        last_order = (
            TimeTable.objects.filter(user=self.user, semester=self.semester)
            .order_by("-order")
            .first()
        )
        if last_order:
            return last_order.order + 1
        return 0

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.pk:  # if instance is being created (not updated)
            self.order = self.get_order()  

        return super().save(force_insert, force_update, using, update_fields)


class TimeTableOpenedSection(models.Model):
    timetable = models.ForeignKey(
        "TimeTable", on_delete=models.CASCADE, related_name="opened_section_entries"
    )
    opened_section = models.ForeignKey(
        "courses.OpenedSection", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.opened_section} in {self.timetable}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["timetable", "opened_section"], name="timetable consists of unique opened sections")
        ]
from django.db import models
from collections import namedtuple

class Institution(models.Model):
    full_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nickname}({self.full_name})"


class Semester(models.Model):
    code = models.IntegerField()

    def __str__(self):
        return str(self.code)
    
class Course(models.Model):
    name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=32)
    credits = models.IntegerField()
    institution = models.ForeignKey("Institution", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.course_code}({self.credits}) {self.name[:20]}...'

class OpenedCourse(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    notes = models.CharField(max_length=600, blank=True)

class Section(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    section_code = models.CharField(max_length=32)

    def __str__(self):
        return f'{self.section_code}'

class OpenedSection(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)
    seats = models.IntegerField("Number of total seats open", blank=True, null=True)
    open_seats = models.IntegerField("Number of open seats currently", blank=True, null=True)
    waitlist = models.IntegerField("Number of people on waitlist with higher priority", blank=True, null=True)
    holdfile = models.IntegerField("Number of people on waitlist with lower priority", blank=True, null=True)

    def __str__(self):
        return f'{self.section} at {self.semester}'

class Instructor(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'

class Teach(models.Model):
    instructor = models.ForeignKey('Instructor', on_delete=models.CASCADE)
    opened_section = models.ForeignKey('OpenedSection', on_delete=models.CASCADE)

class Building(models.Model):
    DEFAULT_LATITUDE = 38.98596
    DEFAULT_LONGITUDE = -76.94457

    full_name = models.CharField('Full Name', max_length=255, blank=True)
    nickname = models.CharField('Short Name', max_length=127)
    latitude = models.FloatField('위도', default=DEFAULT_LATITUDE)
    longitude = models.FloatField('경도', default=DEFAULT_LONGITUDE)

    def __str__(self) -> str:
        return f'{self.nickname}'
    
    def has_coordinates(self):
        return (self.latitude, self.longitude) != (self.DEFAULT_LATITUDE, self.DEFAULT_LONGITUDE)
    
    @property
    def coordinates(self):
        return (self.latitude, self.longitude)


class Location(models.Model):
    room = models.CharField(max_length=32, blank=True)
    building = models.ForeignKey('Building', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.building} {self.room}'

class Duration(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f'{self.start_time} to {self.end_time}'

class Day(models.Model):
    day = models.CharField(max_length=7)

    def __str__(self):
        return f'{self.day}'

class Meeting(models.Model):
    duration = models.ForeignKey('Duration', on_delete=models.CASCADE)
    day = models.ForeignKey('Day', on_delete=models.CASCADE)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    opened_section = models.ForeignKey('OpenedSection', on_delete=models.CASCADE)

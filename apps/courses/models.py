from django.db import models

class Semester(models.Model):
    code = models.IntegerField()

    def __str__(self):
        return str(self.code)
    
class Course(models.Model):
    name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=32)
    credits = models.IntegerField()

    def __str__(self):
        return f'{self.course_code}({self.credits}) {self.name[:20]}...'

class OpenedCourse(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)

class Section(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    section_code = models.CharField(max_length=32)

    def __str__(self):
        return f'{self.section_code}'

class OpenedSection(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)
    seats = models.IntegerField()
    open_seats = models.IntegerField()
    waitlist = models.IntegerField()

    def __str__(self):
        return f'{self.section} at {self.semester}'

class Instructor(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'

class Teach(models.Model):
    instructor = models.ForeignKey('Instructor', on_delete=models.CASCADE)
    opened_section = models.ForeignKey('OpenedSection', on_delete=models.CASCADE)

class Location(models.Model):
    room = models.CharField(max_length=32)
    building = models.CharField(max_length=32)

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

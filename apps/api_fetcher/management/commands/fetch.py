import requests
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime

from apps.courses.models import (
    Semester, 
    Course, 
    OpenedCourse, 
    Section,
    OpenedSection, 
    Instructor, 
    Teach, 
    Location, 
    Duration, 
    Day, 
    Meeting,
)

class Command(BaseCommand):
    help = "Fetch data from UMD API(beta.umd.io) and populate the database."

    def regularize_meeting(self, meetings):
        days = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
        res = []
        for meet in meetings:
            days_in_meet = [d for d in days if d in meet['days']]
            for day in days_in_meet:
                converted_meeting = {}
                converted_meeting['day'] = day

                converted_meeting['duration'] = {}
                converted_meeting['duration']['start_time'] = self.to_time(meet['start_time'])
                converted_meeting['duration']['end_time'] = self.to_time(meet['end_time'])

                converted_meeting['location'] = {}
                converted_meeting['location']['building'] = meet['building']
                converted_meeting['location']['room'] = meet['room']
                res.append(converted_meeting)
        
        return res


    def compare(self, lhs, rhs):
        """
        Compare two meeting objects and return ordering -1, 0, 1 as in <, ==, >
        Order by day - duration__start_time - duration__end_time - location__room - location__building
        """
        if lhs['day'] != rhs.day.day:
            return 1 if (lhs['day'] < rhs.day.day) else -1
        if lhs['duration']['start_time'] != rhs.duration.start_time:
            return 1 if (lhs['duration']['start_time'] < rhs.duration.start_time) else -1
        if lhs['duration']['end_time'] != rhs.duration.end_time:
            return 1 if (lhs['duration']['end_time'] < rhs.duration.end_time) else -1
        if lhs['location']['room'] != rhs.location.room:
            return 1 if (lhs['location']['room'] < rhs.location.room) else -1
        if lhs['location']['building'] != rhs.location.building:
            return 1 if (lhs['location']['building'] < rhs.location.building) else -1
        
        return 0
    
    def populate_opened_sections(self, data):
        """
        
        """
        for section in data:
            course_code = section['course']
            section_code = section['section_id']

            course_obj, _ = Course.objects.get_or_create(course_code=course_code)
            section_obj, _ = Section.objects.get_or_create(course=course_obj, section_code=section_code)

            semester_code = section['semester']
            semester_obj, _ = Semester.objects.get_or_create(code=semester_code)

            opened_section, created = OpenedSection.objects.update_or_create(
                section=section_obj, 
                semester=semester_obj, 
                defaults={
                    'seats': int(section['seats']), 
                    'open_seats': int(section['open_seats']), 
                    'waitlist': int(section['waitlist'])
                })

            # Match incoming and existing instructors

            teaches_with_instructors = Teach.objects.filter(opened_section=opened_section).select_related('instructor')
            teaches_with_instructors = teaches_with_instructors.order_by('instructor__name')

            incoming_instructors = sorted(section['instructors'])
            
            to_add = [] # instructor names that newly teach this section
            to_vanish = [] # teach objects that no longer should exist
            i = 0
            j = 0
            while (i < len(incoming_instructors) and j < len(teaches_with_instructors)):
                incoming = incoming_instructors[i]
                existing = teaches_with_instructors[j].instructor.name

                if (incoming == existing):
                    i = i + 1
                    j = j + 1
                elif incoming > existing:
                    to_vanish.append(teaches_with_instructors[j].instructor)
                    j = j + 1
                else:
                    to_add.append(incoming)
                    i = i + 1
            while (i < len(incoming_instructors)):
                incoming = incoming_instructors[i]
                to_add.append(incoming)
                i = i + 1
            while (j < len(teaches_with_instructors)):
                to_vanish.append(teaches_with_instructors[j].instructor)
                j = j + 1

            for teach in to_vanish:
                teach.delete()
            
            for name in to_add:
                inst, _ = Instructor.objects.get_or_create(name=name)
                Teach.objects.get_or_create(instructor=inst, opened_section=opened_section)
            
            # Match incoming and existing meetings

            existing = Meeting.objects.filter(opened_section=opened_section).select_related('duration', 'day', 'location')
            existing = existing.order_by('day__day', 'duration__start_time', 'duration__end_time', 'location__room', 'location__building')

            incoming = self.regularize_meeting(section['meetings'])

            day_order = {"M": 0, "Tu": 1, "W": 2, "Th": 3, "F": 4, "Sa": 5, "Su": 6}
            ordering = lambda x: (day_order[x['day']], x['duration']['start_time'], x['duration']['end_time'], x['location']['room'], x['location']['building'])
            incoming = sorted(incoming, key=ordering)
            to_add = [] # meeting object to add
            to_vanish = [] # meeting model object to remove
            i = 0
            j = 0
            
            while (i < len(incoming) and j < len(existing)):
                comp = self.compare(incoming[i], existing[j])
                if comp == 0:
                    i = i + 1
                    j = j + 1
                elif comp > 0:
                    to_vanish.append(existing[j])
                    j = j + 1
                else:
                    to_add.append(incoming[i])
                    i = i + 1

            while (i < len(incoming)):
                to_add.append(incoming[i])
                i = i + 1
            while (j < len(existing)):
                to_vanish.append(existing[j])
                j = j + 1
            
            for meet in to_vanish:
                meet.delete()
            for meet in to_add:
                day, _ = Day.objects.get_or_create(day=meet['day'])
                duration, _ = Duration.objects.get_or_create(start_time=meet['duration']['start_time'], 
                                                          end_time=meet['duration']['end_time'])
                location, _ = Location.objects.get_or_create(building=meet['location']['building'], 
                                                          room=meet['location']['room'])
                Meeting.objects.get_or_create(day=day, duration=duration, location=location, opened_section=opened_section)

        self.stdout.write(self.style.SUCCESS("Database populated opened sections successfully."))
                
    def to_time(self, s):
        s = str(s)
        if s.find(':') == 1: 
            s = '0' + s
        return datetime.strptime(s, '%I:%M%p').time()

    def populate_semesters(self, data):
        """ 
        Remove vanished semesters from data, add new semesters from data
        """

        semesters = Semester.objects.all()
        
        i = 0
        j = 0
        to_vanish = [] # list of Semester objects to delete
        to_add = [] # list of semester_codes to add
        
        while i < len(data) and j < len(semesters):
            sem_code_incoming = int(data[j])
            sem_code_existing = semesters[i].code

            if sem_code_incoming == sem_code_existing:
                i = i + 1
                j = j + 1
            elif sem_code_incoming > sem_code_existing:
                to_vanish.append(semesters[j])
                j = j + 1
            else:
                to_add.append(sem_code_incoming)
                i = i + 1
        
        while i < len(data):
            to_add.append(sem_code_incoming)
            i = i + 1
        
        while j < len(semesters):
            to_vanish.append(semesters[j])
            j = j + 1

        # remove all to_vanish
        for sem in to_vanish:
            sem.delete()
        
        for sem_code in to_add:
            Semester.objects.create(code=sem_code)

        

    def populate_courses(self, data):
        for course in data:
            # Extract fields from the data item
            name = course['name']
            course_code = course['course_id']
            credits = course['credits']

            course_obj, _ = Course.objects.update_or_create(course_code=course_code, defaults={'name': name, 'credits': credits})

            semester_code = course['semester']
            semester_obj, _ = Semester.objects.get_or_create(code=semester_code)

            OpenedCourse.objects.get_or_create(semester=semester_obj, course=course_obj)

        self.stdout.write(self.style.SUCCESS("Database populated courses successfully."))

    def populate_from_api(self, initial_url, populate_func, one_page_only):
        url = initial_url

        while url:
            
            retry_cnt = 0
            while (True):
                try: 
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.Timeout as e:
                    self.stdout.write(self.style.WARNING(f'Timeout on {url}'))
                    self.stdout.write(self.style.WARNING(str(e)))

                    if (retry_cnt == 3): 
                        self.stdout.write(self.style.ERROR(f'Stop after {retry_cnt} retries on {url}'))
                        return

                    retry_cnt = retry_cnt + 1
                    self.stdout.write(self.style.WARNING(f'Retry {retry_cnt}'))
                except requests.exceptions.HTTPError as e:
                    self.stdout.write(self.style.ERROR(f'HTTPError on {url}'))
                    self.stdout.write(self.style.ERROR(str(e)))
                    return

            data = response.json()
            self.stdout.write(f"Populate from api: {url}")
            populate_func(data)

            if one_page_only: 
                url = ''
            else:
                url = response.headers.get('X-Next-Page', '')

    def add_arguments(self, parser):
        parser.add_argument('resource_type', type=str, choices=['course', 'section', 'semester'], help='A resource type: course, section, or semester')
        parser.add_argument('--semester', type=int, help='A 6-digit semester number (ex. 202308)')
        parser.add_argument('--test', action='store_true', help='Fetch only the first 100 data if flag is set, otherwise fetch all pages')

    def handle(self, *args, **options):
        resource_type = options['resource_type']
        semester = options['semester']
        one_page_only = options['test']

        if resource_type != 'semester' and not semester:
            raise CommandError(f'The --semester option is required for {resource_type}.')
        if semester is not None and len(str(semester)) != 6:
            raise CommandError('The semester number should be a 6-digit number. (ex. 202308)')
        
        print(f'{resource_type} {semester} {one_page_only}')
        
        if resource_type == 'section':
            url = f"https://api.umd.io/v1/courses/sections?semester={semester}&page=1&per_page=100"
            self.populate_from_api(url, self.populate_opened_sections, one_page_only=one_page_only)
        elif resource_type == 'course':
            url = f"https://api.umd.io/v1/courses?semester={semester}&page=1&per_page=100"
            self.populate_from_api(url, self.populate_courses, one_page_only=one_page_only)
        elif resource_type == 'semester':
            url = f"https://api.umd.io/v1/courses/semesters"
            self.populate_from_api(url, self.populate_semesters, one_page_only=True)

        self.stdout.write(self.style.SUCCESS(f'Successfully fetched {resource_type} data for semester {semester} with one_page_only={one_page_only}'))

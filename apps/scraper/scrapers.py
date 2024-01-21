from datetime import datetime
import requests
from bs4 import BeautifulSoup

from apps.courses.models import Building, Course, Day, Duration, Institution, Instructor, Location, Meeting, OpenedCourse, OpenedSection, Section, Semester, Teach

class UMDScraper:
    BASE_URL = "https://app.testudo.umd.edu/soc/"
    semesters = None
    INSTITUTION_FULL_NAME = "University of Maryland"
    INSTITUTION_NICKNAME = "UMD"

    def run(self, test=False):
        sems = self.get_semesters()
        if test: 
            sems = [s for s in sems if str(s).endswith("12")]
            sems = sems[0:1]
        
        for sem in sems:
            self.run_semester(sem, test)
    
    def run_semester(self, sem: int, test=False):
        """
        :params
            sem: Semester code
        """
        sems = self.get_semesters()
        if sem not in sems: 
            raise ValueError(f"Invalid semester {sem}")

        deps = self.get_departments(sem)
        if test: deps = ['CMSC']
        for idx, dep in enumerate(deps):
            if idx+1 <= 10: continue
            open_sections_data = self.get_department_open_sections(sem, dep)
            self.save(sem, open_sections_data)
            print(f'Save {dep} in term {sem} finished ({idx+1}/{len(deps)})')


    def get_semesters(self) -> list[int]:
        """
        Get a list of semesters provided in source website, in this case, Testudo.

        :return
            a list of integers that represent semesters(terms). ex) [202308, 202312]
        """

        if self.semesters is not None: 
            return self.semesters

        # Use requests to get the HTML content of the website
        response = requests.get(self.BASE_URL)
        # Check if the request was successful
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the select tag with the given selector
        terms_select_tag = soup.find("select", id="term-id-input")
        # Initialize an empty list to store the values
        sems = []
        # Loop through the option tags inside the select tag
        for term_option_tag in terms_select_tag.find_all("option"):
            # Get the value attribute of each option tag
            sem = term_option_tag["value"]
            # Convert the value to an integer and append it to the list
            try:
                sems.append(int(sem))
            except (ValueError, TypeError):
                print(f"Invalid value {sem} found as semester. Ignoring value.")
                continue
        # Return the list of values
        self.semesters = sems
        return sems


    def get_departments(self, sem: int) -> list[str]:
        """
        Get a list of department codes from a specific semester
        :params
            sem: semester code
        """
        sems = self.get_semesters()
        if sem not in sems: 
            raise ValueError(f"Invalid semester {sem}")

        # Make a GET request to the website with the semester parameter
        response = requests.get(self.BASE_URL + str(sem))
        # Check for valid response by calling raise_for_status()
        response.raise_for_status()
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the div tag with the given selector
        deps_div_tag = soup.find("div", id="course-prefixes-page")
        # Initialize an empty list to store the codes
        codes = []
        # Loop through the div tags with class "course-prefix row" under the div tag
        for dep_div_tag in deps_div_tag.find_all("div", class_="course-prefix row"):
            # Find the a tag under each row
            a = dep_div_tag.find("a")
            # Get the href attribute of the a tag
            href = a["href"]
            # Split the href by "/" and get the second part
            dep_code = href.split("/")[1]
            # Append the code to the list
            codes.append(dep_code)
        # Return the list of codes
        return codes


    def get_department_open_sections(self, sem: int, dep: str):
        """
        :params:
            sem: semester code
            dep: department code
        :returns:
            the list of open sections in semester `sem` and department `dep`.
            each open section has the following form. 
            ```json
            {
                "course": {
                    "name"
                    "code"
                    "credits"
                    "restriction"
                    "prerequisite"
                    "notes"
                },
                "sections": [
                    {
                        "code"
                        "seats"
                        "open_seats"
                        "waitlist"
                        "holdfile": 
                        "instructors": list
                        "meetings": [
                            {
                                "days": str
                                "start_time": str
                                "end_time": str
                                "bldg": str
                                "room": str
                            },
                            ...
                        ]
                        "duration": "MWF 10:00am - 10:50am"
                        "location": "WDS 1114"
                    },
                    ...
                ]
            }
            ```
        """
        url = self.BASE_URL + "search"
        params = {
            "courseId": dep,
            "sectionId": "",
            "termId": str(sem),
            "_openSectionsOnly": "on",
            "creditCompare": ">=",
            "credits": "0.0",
            "courseLevelFilter": "UGRAD", # undergraduate
            "instructor": "",
            "_facetoface": "on",
            "_blended": "on",
            "_online": "on",
            "courseStartCompare": "",
            "courseStartHour": "",
            "courseStartMin": "",
            "courseStartAM": "",
            "courseEndHour": "",
            "courseEndMin": "",
            "courseEndAM": "",
            "teachingCenter": "ALL",
            "_classDay1": "on",
            "_classDay2": "on",
            "_classDay3": "on",
            "_classDay4": "on",
            "_classDay5": "on"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        courses = []
        soup = BeautifulSoup(response.content, "html.parser")
        container = soup.select_one("div.course-prefix-container div.courses-container")
        if container is None:
            return []
        course_divs = container.find_all("div", recursive=False)
        for course_div in course_divs:
            # Get course info like course code, name, credits, and notes including restriction, prerequisite and more
            code = course_div.select_one("div.course-id-container.one.columns div.course-id")
            if code is None: continue
            code = code.string
            name = course_div.select_one("div.course-info-container.eleven.columns div.course-basic-info-container.sixteen.colgrid span.course-title")
            if name is None: continue
            name = name.string
            credits = course_div.select_one("div.course-info-container.eleven.columns div.course-basic-info-container.sixteen.colgrid span.course-min-credits")
            if credits is None: continue
            credits = int(credits.string)

            notes = str()
            course_detail = course_div.select("div.course-info-container.eleven.columns > div.approved-course-texts-container > div:nth-child(1) > div > div > div > div")
            if len(course_detail) > 0: 
                course_detail = course_detail[0].find_all("div", recursive=False)
                for course_detail_item in course_detail:
                    crs_detail = course_detail_item.get_text(strip=True, separator=" ")
                    if len(crs_detail) > 0:
                        notes += f"\n{crs_detail}"
            
            # Gen Ed
            gen_ed = course_div.select("div.course-info-container.eleven.columns > div.course-basic-info-container.sixteen.colgrid > div.course-stats-container.row.clearfix > div.gen-ed-codes-group.six.columns > div")
            if len(gen_ed) > 0: 
                gen_ed = gen_ed[0].get_text(strip=True)
                if len(gen_ed) > 0:
                    notes += f"\n{gen_ed}"

            # Core
            core = course_div.select("div.course-info-container.eleven.columns > div.course-basic-info-container.sixteen.colgrid > div.course-stats-container.row.clearfix > div.core-codes-group.two.columns > div")
            if len(core) > 0:
                core = core[0].get_text(strip=True)
                if len(core) > 0:
                    notes += f"\n{core}"

            # Course text in some courses
            course_text = course_div.select("div.course-info-container.eleven.columns > div.course-texts-container > div > div > div")
            if len(course_text) > 0:
                course_text = course_text[0].find(text=True, recursive=False)
                if course_text is not None and len(course_text) > 0: 
                    notes += f"\n{course_text}"
            
            course = {
                "code": code,
                "name": name,
                "credits": credits,
                "notes": notes.strip()
            }
            
            # Get section info of this course, such as section code, instructor and more
            sections = []
            sections_container_div = course_div.select_one('div.course-info-container.eleven.columns > div.toggle-sections-link-container > div > div > fieldset > div > div.sections')
            if sections_container_div is None:
                # no open section for this course
                continue
            
            sections_div = sections_container_div.find_all("div", recursive=False)
            for section_div in sections_div:
                section = dict()
                # get section code, instructors, seats
                section_info_div = section_div.select_one("div.section-info-container > div")
                section['code'] = str(section_info_div.find("span", class_="section-id").string).strip()
                section['code'] = course['code'] + '-' + section['code']
                instructors_span = section_info_div.find("span", class_="section-instructors").find_all("span", class_="section-instructor")
                section['instructors'] = list()
                for inst in instructors_span:
                    section['instructors'].append(str(inst.string).strip())
                seats_info_span = section_info_div.select_one('div.seats-info-group.six.columns > div > span.seats-info')
                seats = seats_info_span.select_one('span.seats-info span.total-seats-count')
                if seats is not None:
                    section['seats'] = int(seats.string)
                open_seats = seats_info_span.select_one('span.open-seats span.open-seats-count')
                if open_seats is not None:
                    section['open_seats'] = int(open_seats.string)
                waitlist_holdfile = seats_info_span.select('span.waitlist span.waitlist-count')
                if len(waitlist_holdfile) == 2:
                    section['waitlist'] = int(waitlist_holdfile[0].string)
                    section['holdfile'] = int(waitlist_holdfile[1].string)
                elif len(waitlist_holdfile) == 1:
                    section['waitlist'] = int(waitlist_holdfile[0].string)
                    section['holdfile'] = None
                else:
                    section['waitlist'] = None
                    section['holdfile'] = None
                
                # get section meeting(hours, location)
                section['meetings'] = list()
                
                section_meetings_div = section_div.select_one('div.class-days-container')
                if section_meetings_div is None:
                    continue
                section_meetings_div = section_meetings_div.find_all('div', class_='row')
                for section_meeting_div in section_meetings_div:
                    meeting = dict()
                    days = section_meeting_div.select_one('span.section-days')
                    if days is not None: meeting['days'] = days.string
                    start_time = section_meeting_div.select_one('span.class-start-time')
                    if start_time is not None: meeting['start_time'] = start_time.string
                    end_time = section_meeting_div.select_one('span.class-end-time')
                    if end_time is not None: meeting['end_time'] = end_time.string
                    bldg = section_meeting_div.select_one('span.building-code')
                    if bldg is not None: meeting['bldg'] = bldg.string
                    room = section_meeting_div.select_one('span.class-room')
                    if room is not None: meeting['room'] = room.string
                    section['meetings'].append(meeting)
                sections.append(section)
            
            course['sections'] = sections
            courses.append(course)

        return courses

    def to_time(self, s):
        s = str(s)
        if s.find(':') == 1: 
            s = '0' + s
        return datetime.strptime(s, '%I:%M%p').time()

    def regularize_meetings(self, meetings):
        """
        :params
            meetings: a list of meetings in the form
                {
                    "days": "MW",
                    "start_time": "12:00pm",
                    "end_time": "12:50pm",
                    "bldg": "CSI",
                    "room": "2117"
                }
        :returns
            a list of meetings in the form
                {
                    "day": "M", 
                    "start_time": Python time object of 12pm,
                    "end_time": Python time object of 12:50pm,
                    "bldg": "CSI",
                    "room": "2117",
                },
                {
                    "day": "W",
                    "start_time": Python time object of 12pm,
                    "end_time": Python time object of 12:50pm,
                    "bldg": "CSI",
                    "room": "2117",
                }
        """
        days = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']
        regularized = []
        for m in meetings:
            days_in_m = [d for d in days if d in m.get('days', '')]
            start_time = None if m.get('start_time') is None else self.to_time(m.get('start_time'))
            end_time = None if m.get('start_time') is None else  self.to_time(m.get('end_time'))
            bldg = 'ONLINE' if m.get('room') == 'ONLINE' else m.get('bldg')
            room = '' if (m.get('room') == 'ONLINE' or not m.get('room')) else m.get('room')
            for d in days_in_m:
                reg_meeting = {
                    'day': d,
                    'start_time': start_time,
                    'end_time': end_time,
                    'bldg': bldg,
                    'room': room,
                }
                regularized.append(reg_meeting)
        return regularized

    def save(self, semester: int, open_sections_data: list[dict]):
        """
        :params
            sem: the semester of the open sections data
            open_sections_data: list of dict about open sections that follows the form
                ```json
                {
                    "code": "CMSC100",
                    "name": "Bits and Bytes of Computer and Information Sciences",
                    "credits": 1,
                    "notes": "Restriction: For first time freshmen and first time transfer students.",
                    "sections": [
                        {
                            "code": "0101",
                            "instructors": [
                                "Jenyia Wilson"
                            ],
                            "seats": 40,
                            "open_seats": 15,
                            "waitlist": 0,
                            "holdfile": null,
                            "meetings": [
                                {
                                    "days": "M",
                                    "start_time": "12:00pm",
                                    "end_time": "12:50pm",
                                    "bldg": "CSI",
                                    "room": "2117"
                                }
                            ]
                        },
                    ]
                }
                ```
        """
        
        institution, _ = Institution.objects.get_or_create(full_name=self.INSTITUTION_FULL_NAME, nickname=self.INSTITUTION_NICKNAME)
        sem, _ = Semester.objects.get_or_create(code=semester)

        for crs in open_sections_data:
            course, _ = Course.objects.get_or_create(
                name=crs.get('name'),
                course_code=crs.get('code'),
                credits=crs.get('credits'),
                institution=institution,
            )
            
            opened_course, _ = OpenedCourse.objects.update_or_create(
                course=course,
                semester=sem,
                defaults={'notes': str(crs.get('notes'))[:600]}
            )

            for section in crs.get('sections'):
                sec, _ = Section.objects.get_or_create(
                    course=course,
                    section_code=section.get('code'),
                )

                opened_section, _ = OpenedSection.objects.update_or_create(
                    semester=sem,
                    section=sec,
                    defaults={
                        'seats': section.get('seats'),
                        'open_seats': section.get('open_seats'),
                        'waitlist': section.get('waitlist'),
                        'holdfile': section.get('holdfile')
                    }
                )

                # Update instructors
                latest_teach = set()
                for inst in section.get('instructors'):
                    # 1. get or create latest instructors
                    i, _ = Instructor.objects.get_or_create(
                        name=inst
                    )
                    # 2. get or create latest teach
                    t, _ = Teach.objects.get_or_create(
                        instructor=i,
                        opened_section=opened_section
                    )
                    # 3. let latest_teach be the set of latest teach objects
                    latest_teach.add(t)
                
                # 4. let old_teach be the set of old teach objects
                old_teach = set(Teach.objects.filter(
                    opened_section=opened_section
                ))

                # 5. remove old_teach - latest_teach
                remove_teach = old_teach - latest_teach
                remove_teach_ids = [r.id for r in remove_teach]
                Teach.objects.filter(id__in=remove_teach_ids).delete()
                
                # Update meetings
                latest_meetings = set()
                meetings = self.regularize_meetings(section.get('meetings'))
                for m in meetings:
                    # get or create the components of a meeting
                    bldg, _ = Building.objects.get_or_create(nickname=m.get('bldg'))
                    loc, _ = Location.objects.get_or_create(building=bldg, room=m.get('room'))
                    dur, _ = Duration.objects.get_or_create(start_time=m.get('start_time'), end_time=m.get('end_time'))
                    day, _ = Day.objects.get_or_create(day=m.get('day'))
                    latest_m, _ = Meeting.objects.get_or_create(duration=dur, day=day, location=loc, opened_section=opened_section)
                    # let latest_meetings be the set of latest Meeting objects
                    latest_meetings.add(latest_m)
                
                old_meetings = set(Meeting.objects.filter(
                    opened_section=opened_section
                ))
                # remove old_meetings - latest_meetings
                remove_meetings = old_meetings - latest_meetings
                remove_meetings_ids = [m.id for m in remove_meetings]
                Meeting.objects.filter(id__in=remove_meetings_ids).delete()

scrapers = {
    "University of Maryland": UMDScraper()
}
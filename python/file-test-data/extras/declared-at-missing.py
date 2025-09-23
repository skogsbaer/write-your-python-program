from wypp import *

@record
class Course:
    name: str
    teacher: str
    students: tuple[str, ...]

@record(mutable=True)
class CourseM:
    name: str
    teacher: str
    students: tuple[str, ...]

@record
class Semester:
    degreeProgram: str
    semester: str
    courses: tuple[CourseM, ...]

prog1 = Course('Programmierung 1', 'Wehr', ())
semester1_2020 = Semester('AKI', '1. Semester 2020/21', (prog1, ))

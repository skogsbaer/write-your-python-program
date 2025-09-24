from wypp import *

@record(mutable=True)
class CourseM:
    name: str
    teacher: str
    students: list[str]

x = CourseM('Grundlagen der Informatik', 'Oelke', [])
print(x)

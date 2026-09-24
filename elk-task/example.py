from wypp import *

@record
class Student:
    name: str
    grade: float

@record
class Subject:
    name: str
    students: list[Student]


tim = Student('Tim', 1.0)
karl = Student('karl', 2.0)
tom = Student('Tom', 1.3)
karl2 = Student('karl', 2.6)
mariam = Student('Mariam', 1.0)
hector = Student('Hector', 3.0)
quentin = Student('Quentin', 1.7)
fabio = Student('Fabio', 4.0)
jonas = Student('Jonas', 5.0)
lara = Student('Lara', 3.3)
gerd = Student('Gerd', 2.6)
joerg = Student('Joerg', 2.6)

aud = Subject('AuD', [tim, karl, tom, karl2, mariam, hector, quentin, fabio, jonas, lara, gerd, joerg])
prog1 = Subject('Prog1', [lara, quentin, jonas, fabio, hector, gerd])

subjectList = [aud, prog1]

def createGradeList(subject: Subject) -> list[float]:
    result = [float]
    for student in subject.students:
        result.append(student.grade)
    return result

gradeList = createGradeList(prog1)
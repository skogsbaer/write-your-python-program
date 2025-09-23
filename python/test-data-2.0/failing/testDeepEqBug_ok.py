from wypp import *

# Ein Kurs hat:
# - einen Namen
# - eine Dozentin / ein Dozent
# - eine Liste von Matrikelnummer für die angemeldeten Studierenden.
@record(mutable=True)
class CourseM:
    name: str
    teacher: str
    students: list[str]
    # Operation zum eines Studierenden zum Kurs
    # Eingabe: Matrikelnummer
    # Ergebnis: nichts
    # SEITENEFFEKT: Studierende ist nachher in der Liste des Kurses drin
    def addStudent(self, matrikel: str) -> None:
        if matrikel not in self.students:
            self.students.append(matrikel)

csBasicsM = CourseM('Grundlagen der Informatik', 'Oelke', [])
csBasicsM.addStudent('1234')
#check(csBasicsM, CourseM('Grundlagen der Informatik', 'Oelke', ['1234']))

# Ein Semester eines Studiengangs besteht aus:
# - Name des Studiengangs
# - Name des Semesters
# - potentiell mehreren Kursen.
@record(mutable=True)
class SemesterM:
    degreeProgram: str
    semester: str
    courses: list[CourseM]

    # Operation zum Hinzufügen eines Studierenden zu einem Semester,
    # Eingaben: Name des Kurses und die Matrikelnummer
    # Ergebnis: nichts
    # SEITENEFFEKT: Studierende ist nachher in der Liste des Kurses drin.
    def addStudent(self, courseName: str, matrikel: str) -> None:
        for c in self.courses:
            if c.name == courseName:
                c.addStudent(matrikel)

prog1M = CourseM('Programmierung 1', 'Wehr', [])
semester1_2020 = SemesterM('AKI', '1. Semester 2020/21', [prog1M, csBasicsM])
semester1_2021 = SemesterM('AKI', '1. Semester 2021/22', [prog1M, csBasicsM])
semester1_2020.addStudent('Programmierung 1', '1234')
semester1_2020.addStudent('Programmierung 1', '9876')
# check(semester1_2020,
#       SemesterM('AKI',
#                 '1. Semester 2020/21',
#                 [CourseM('Programmierung 1', 'Wehr', ['1234', '9876']), csBasicsM]))

# The following test should fail.
# The bug is: it cause a stack overflow:
#   Traceback (most recent call last):
#     File "test-data/testDeepEqBug.py", line 52, in <module>
#       check(semester1_2021,
#     File "<string>", line 4, in __eq__
#     File "<string>", line 4, in __eq__
#   RecursionError: maximum recursion depth exceeded in comparison
check(semester1_2021,
      SemesterM('AKI',
                '1. Semester 2021/22',
                [CourseM('Programmierung 1', 'Wehr', []),
                 CourseM('Grundlagen der Informatik', 'Oelke', [])]))

from wypp import *

# Definition-of-done case: the trace ends in an exception.
# The visualization must still render every step up to the failure, show the
# traceback in the output pane, and not break on the partial trace.

@record
class Student:
    name: str
    grade: float


students = [Student('Anna', 1.0), Student('Ben', 2.3)]
grades = []

for student in students:
    grades.append(student.grade)

# Fails: only two grades were collected.
third = grades[2]
print(third)

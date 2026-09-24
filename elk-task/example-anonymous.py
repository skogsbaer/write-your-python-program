from wypp import *

# Definition-of-done case: objects that are reachable ONLY through another object.
#
# In example.py every Student is also bound to a module-level global, so it stays
# reachable from a stack root no matter what you collapse - collapsing a list there
# hides edges but removes no nodes. Here nothing inside the containers has a name of
# its own, so collapsing the container must make its contents disappear.

@record
class Student:
    name: str
    grade: float


# Nested lists, no names on the inner lists.
# Collapsing `data` must remove both inner lists.
data = [[1, 2], [3, 4]]

# Anonymous instances. Collapsing `group` must remove both Students.
group = [Student('Anna', 1.0), Student('Ben', 2.3)]

# One shared object for contrast: `shared` keeps its own name, so collapsing
# `holder` must NOT remove it.
shared = Student('Cleo', 1.7)
holder = [shared]

# A container that is itself anonymous: only reachable through `outer`.
outer = [[shared, Student('Dan', 3.0)]]


def summarize(students: list[Student]) -> list[float]:
    grades = []
    for student in students:
        grades.append(student.grade)
    return grades


groupGrades = summarize(group)

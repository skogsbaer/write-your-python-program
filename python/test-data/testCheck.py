from wypp import *

@record
class Point:
    x: int
    y: int

@record
class Name:
    firstName: str
    lastName: str

check(1, 2)
check('abc', 'xyz')
check(Point(1,2), Point(1,3))
check(Name('Max', 'Müller'), Point(1,3))

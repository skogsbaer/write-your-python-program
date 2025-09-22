from wypp import *

@record(mutable=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
p.x = 5
print('ok')

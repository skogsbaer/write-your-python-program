from wypp import *

@record
class Point:
    x: int
    y: int
    z: int

# The keyword argument y must be highlighted
p = Point(1, z=3, y='zwei')

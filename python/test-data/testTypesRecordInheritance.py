from wypp import *

@record
class Point2D:
    x: int
    y: int

@record
class Point3D(Point2D):
    z: int

print(Point3D(1,2,3))
Point3D(1,2, "foo")


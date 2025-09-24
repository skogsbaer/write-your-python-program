from wypp import *

@record
class C:
    x: int
    y: int = 0

c1 = C(1)
c2 = C(1, 2)
print('ok')

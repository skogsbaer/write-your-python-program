from wypp import *

type OnOff = Literal['on', 'off']

def test(x: OnOff):
    pass

test('blub')

@record
class Point:
    x: int
    y: int

p = Point(1, 2)
print(p)

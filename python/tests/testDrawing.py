import unittest
from writeYourProgram import *
from drawingLib import *

setDieOnCheckFailures(True)

class TestDrawing(unittest.TestCase):

    def test_drawing(self):
        shapes = [
            FixedShape('rectangle', 'red', Size(3, 1), Point(-1, 1.5)),
            FixedShape('ellipsis', 'blue', Size(2, 3), Point(-1, -0.5)),
            FixedShape('rectangle', 'black', Size(2, 2), Point(1.5, 0))
        ]
        # Do not draw, does not work with CI
        # drawFixedShapes(shapes, stopAfter=0.5)

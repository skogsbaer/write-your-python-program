# Run this file with the debugger to debug wypp.
# Before running, set FILE to the input file that you want
# to use for debugging.

FILE = 'test-data/testNums.py'

import os
import sys

thisDir = os.path.dirname(__file__)
file = os.path.join(thisDir, FILE)
args = [file]

sys.path.insert(0, os.path.join(thisDir, 'code'))

from wypp import runner # type: ignore
runner.main(globals(), args)

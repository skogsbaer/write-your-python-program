import unittest
import sys
import types
import stacktrace
from stacktraceTestData import *
import os

class TestReturnTracker(unittest.TestCase):

    def setUp(self):
        # Save original profile function
        self.original_profile = sys.getprofile()

    def tearDown(self):
        # Restore original profile function
        sys.setprofile(self.original_profile)

    def assertReturnFrame(self, tracker: stacktrace.ReturnTracker, line: int):
        frame = tracker.getReturnFrame()
        assert(frame is not None)
        self.assertEqual(os.path.basename(frame.filename), 'stacktraceTestData.py')
        self.assertEqual(frame.lineno, line)

    def test_returnTracker1(self):
        tracker = stacktrace.installProfileHook()
        f1()
        self.assertReturnFrame(tracker, f1ReturnLine)

    def test_returnTracker2(self):
        tracker = stacktrace.installProfileHook()
        f2()
        self.assertReturnFrame(tracker, f2ReturnLine)

    def test_returnTracker3(self):
        tracker = stacktrace.installProfileHook()
        f3()
        self.assertReturnFrame(tracker, f3ReturnLine)

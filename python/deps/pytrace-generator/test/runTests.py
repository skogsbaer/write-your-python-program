import json
import os
import subprocess
import unittest

from util import read_trace_entries

class TestTraceGeneration(unittest.TestCase):
    pass

def generate_test(python_file, expected_trace_path):
    def test(self):
        p = subprocess.run(
            ["python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), python_file],
            capture_output=True
        )
        self.assertEqual(p.returncode, 0)
        if expected_trace_path is not None:
            trace_entries = read_trace_entries(p.stdout)
            with open(expected_trace_path) as f:
                expected_trace = json.load(f)
            self.assertEqual(trace_entries, expected_trace)

    return test

if __name__ == '__main__':
    test_cases_dir = os.path.join(os.path.dirname(__file__), "test-cases")
    with os.scandir(test_cases_dir) as scan:
        for entry in scan:
            if not entry.is_file() or not entry.name.endswith(".py"):
                continue
            json_path = f"{entry.path}.json"
            if not os.path.isfile(json_path):
                json_path = None
            test_name = f'test_{entry.name[:-3]}'
            test = generate_test(entry.path, json_path)
            setattr(TestTraceGeneration, test_name, test)
    unittest.main()

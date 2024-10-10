import json
import os
import socket
import subprocess
import unittest

from util import read_trace_entries

class TestTraceGeneration(unittest.TestCase):
    pass

def generate_test(python_file, expected_trace_path):
    def test(self):
        trace_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        trace_socket.bind(("127.0.0.1", 0))
        trace_socket.listen(1)
        port = trace_socket.getsockname()[1]
        p = subprocess.Popen(
            ["python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), python_file, str(port)]
        )
        connection, address = trace_socket.accept()
        data = bytearray()
        while True:
            buf = connection.recv(4096)
            if len(buf) == 0:
                break
            data.extend(buf)
        connection.close()
        trace_socket.close()
        returncode = p.wait()
        self.assertEqual(returncode, 0)
        if expected_trace_path is not None:
            trace_entries = read_trace_entries(data)
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

import json
import os
import subprocess
import sys

from util import read_trace_entries

if __name__ == '__main__':
    python_file = sys.argv[1]
    trace_file = f"{sys.argv[1]}.json"
    p = subprocess.run(
        ["python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), python_file],
        capture_output=True
    )
    if p.returncode != 0:
        raise RuntimeError("trace generator did not exit with exit code 0")
    trace_entries = read_trace_entries(p.stdout)
    with open(trace_file, "w") as f:
        json.dump(trace_entries, f, indent="\t")

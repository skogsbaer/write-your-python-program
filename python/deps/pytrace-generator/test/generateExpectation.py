import json
import os
import socket
import subprocess
import sys

from util import read_trace_entries

if __name__ == '__main__':
    python_file = sys.argv[1]
    trace_file = f"{sys.argv[1]}.json"
    trace_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    trace_socket.bind(("127.0.0.1", 0))
    trace_socket.listen(1)
    port = trace_socket.getsockname()[1]
    p = subprocess.run(
        ["python3", os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), python_file, str(port)],
        capture_output=True
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
    if p.returncode != 0:
        raise RuntimeError("trace generator did not exit with exit code 0")
    trace_entries = read_trace_entries(data)
    with open(trace_file, "w") as f:
        json.dump(trace_entries, f, indent="\t")

import json

def read_trace_entries(data):
    entries = []
    while len(data) > 0:
        entry_len = int.from_bytes(data[:4], byteorder="big", signed=False)
        data = data[4:]
        entry = json.loads(str(data[:entry_len], encoding="utf-8"))
        test_cases_str = "test-cases/"
        idx = entry["filePath"].rfind(test_cases_str)
        if idx >= 0:
            # Remove user specific path stuff to allow for equality testing
            entry["filePath"] = entry["filePath"][idx + len(test_cases_str):]
        entries.append(entry)
        data = data[entry_len:]
    return entries

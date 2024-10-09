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
        normalize_refs(entry)
        entries.append(entry)
        data = data[entry_len:]
    return entries

def normalize_refs(entry):
    next_id = 0
    mapping = {}
    for frame in entry["stack"]:
        for var in frame["locals"]:
            if var["type"] == "ref":
                original_id = var["value"]
                if original_id in mapping:
                    var["value"] = mapping[original_id]
                else:
                    var["value"] = next_id
                    mapping[original_id] = next_id
                    if str(next_id) in entry["heap"]:
                        tmp = entry["heap"][str(next_id)]
                        entry["heap"][str(next_id)] = entry["heap"][str(original_id)]
                        entry["heap"][str(original_id)] = tmp
                    else:
                        entry["heap"][str(next_id)] = entry["heap"][str(original_id)]
                        del entry["heap"][str(original_id)]
                    next_id += 1

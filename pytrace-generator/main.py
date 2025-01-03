import bdb
import copy
from dataclasses import dataclass
import inspect
import io
import json
import linecache
import math
import os
import re
import socket
import sys
import traceback
import types
import typing

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

type_name_regex = re.compile("<class '(?:__main__\\.)?(.*)'>")
function_str_regex = re.compile(r"^(<function .+) at .+>")
import_regex = re.compile(r"^(?:[^'\"]+\s)?import[\s*]")

# Frame objects:
# https://docs.python.org/3/reference/datamodel.html#frame-objects

STACK_TYPES = {
    int: "int",
    float: "float",
    bool: "bool",
    str: "str",
    type(None): "none",
    type: "type",
    typing.TypeAliasType: "type",
    types.FunctionType: "function"
}
HEAP_TYPES = {
    list: "list",
    tuple: "tuple",
    dict: "dict",
    set: "set"
}

def primitive_type(t):
    try:
        return STACK_TYPES[t]
    except KeyError:
        return "ref"

def complex_type(t):
    try:
        return STACK_TYPES[t]
    except KeyError:
        try:
            return HEAP_TYPES[t]
        except KeyError:
            return "instance"

class HeapValue:
    def __init__(self, value, value_type=None, key_lookup_table=None):
        self.value = value
        self.value_type = value_type
        if value_type is None:
            self.type_str = complex_type(type(value))
        else:
            self.type_str = complex_type(value_type)
        self.key_lookup_table = key_lookup_table

    def format(self):
        value_type = type(self.value)
        value_fmt = self.value
        if value_type == list:
            value_fmt = [v.format() for v in self.value]
        elif value_type == dict:
            value_fmt = {k: v.format() for k, v in self.value.items()}

        result = {
            "type": self.type_str,
            "value": value_fmt
        }

        if self.key_lookup_table is not None:
            key_lookup_table_fmt = {k: v.format() for k, v in self.key_lookup_table.items()}
            result["keys"] = key_lookup_table_fmt

        if self.type_str == "instance":
            type_name = str(self.value_type)
            search_result = type_name_regex.search(type_name)
            if search_result is not None:
                type_name = search_result.group(1)
            result["name"] = type_name

        return result

class PrimitiveValue:
    def __init__(self, value, variable_name=None):
        self.variable_name = variable_name
        self.type_str = primitive_type(type(value))
        if self.type_str == "ref":
            self.value = id(value)
        elif type(value) == float and math.isnan(value):
            self.value = "NaN" # Hack because NaN could otherwise not be represented in JSON
        elif type(value) == float and math.isinf(value):
            # Hack because Infinity could otherwise not be represented in JSON
            if value > 0:
                self.value = "Infinity"
            else:
                self.value = "Negative Infinity"
        else:
            self.value = value

    def is_ref(self):
        return self.type_str == "ref"

    def format(self):
        d = {
            "type": self.type_str,
            "value": self.value
        }
        if type(d["value"]) == type:
            type_name = str(d["value"])
            search_result = type_name_regex.search(type_name)
            if search_result is not None:
                type_name = f"<class '{search_result.group(1)}'>"
            d["value"] = type_name
        elif type(d["value"]) == typing.TypeAliasType:
            d["value"] = "<TypeAlias>"
        elif inspect.isfunction(d["value"]):
            function_desc = str(d["value"])
            search_result = function_str_regex.search(function_desc)
            if search_result is not None:
                function_desc = f"{search_result.group(1)}>"
            d["value"] = function_desc
        if self.variable_name is not None:
            d["name"] = self.variable_name
        return d

class StackFrame:
    def __init__(self, name):
        self.name = name
        self.values = []

    def push(self, variable_name, value):
        value_index = None
        for idx, stack_value in enumerate(self.values):
            if stack_value.variable_name == variable_name:
                value_index = idx
                break

        stack_value = PrimitiveValue(value, variable_name)
        if value_index is not None:
            self.values[value_index] = stack_value
        else:
            self.values.append(stack_value)

    def format(self):
        return {
            "frameName": self.name,
            "locals": [value.format() for value in self.values]
        }

class Stack:
    def __init__(self):
        self.frames = []

    def push_frame(self, frame):
        self.frames.append(StackFrame(frame.f_code.co_qualname))

    def pop_frame(self):
        self.frames.pop()

    def push(self, variable_name, value):
        self.frames[-1].push(variable_name, value)

    def format(self):
        return [frame.format() for frame in self.frames]

    def contains(self, variable_name):
        for frame in self.frames:
            for var in frame.values:
                if var.variable_name == variable_name:
                    return True
        return False

class Heap:
    def __init__(self, script_path):
        self.script_path = script_path
        self.memory = {}

    def store(self, address, value):
        # This check only works because we are taking heap snapshots
        if address in self.memory:
            # Prevents cycles due to cyclic references
            return

        value_type = type(value)
        stored_value = value
        key_lookup_table = None
        inner_values = []
        if value_type == list or value_type == tuple or value_type == set:
            stored_value = []
            for elem in value:
                prim_value = PrimitiveValue(elem)
                stored_value.append(prim_value)
                if prim_value.is_ref():
                    inner_values.append(elem)
        elif value_type == dict:
            stored_value = {}
            key_lookup_table = {}
            for k, v in value.items():
                key_id = id(k)

                key_value = PrimitiveValue(k)
                key_lookup_table[key_id] = key_value
                if key_value.is_ref():
                    inner_values.append(k)

                prim_value = PrimitiveValue(v)
                stored_value[key_id] = prim_value
                if prim_value.is_ref():
                    inner_values.append(v)
        elif inspect.isgenerator(value):
            stored_value = {}
        else:
            # Assume that there are no primitive types (int, bool, ...) passed to the top level heap
            # Only "real" objects are left
            stored_value = {}
            for field in dir(value):
                try:
                    v = getattr(value, field)
                except:
                    # Just ignore it in case getattr fails
                    continue
                if should_ignore_on_heap(field, v, self.script_path):
                    continue

                prim_value = PrimitiveValue(v)
                stored_value[field] = prim_value
                if prim_value.is_ref():
                    inner_values.append(v)
        self.memory[address] = HeapValue(stored_value, value_type, key_lookup_table)

        # Store inner elements
        for inner in inner_values:
            self.store(id(inner), inner)

    def format(self):
        return {k: v.format() for k, v in self.memory.items()}

@dataclass
class TraceStep:
    line: int
    file_path: str
    stack: Stack
    heap: Heap
    stdout: str
    traceback_text: str

    def format(self):
        step = {
            "line": self.line,
            "filePath": self.file_path,
            "stack": self.stack.format(),
            "heap": self.heap.format(),
            "stdout": self.stdout,
        }
        if self.traceback_text is not None:
            step["traceback"] = self.traceback_text
        return step


def should_ignore(variable_name, value, script_path, ignore_list = []):
    if variable_name in ignore_list or variable_name.startswith("__"):
        return True
    if inspect.isbuiltin(value):
        return True
    if inspect.ismodule(value):
        return True
    if inspect.isframe(value):
        return True
    return False

def should_ignore_on_stack(variable_name, value, script_path, ignore_list = []):
    if should_ignore(variable_name, value, script_path, ignore_list):
        return True
    return False

def should_ignore_on_heap(variable_name, value, script_path, ignore_list = []):
    if should_ignore(variable_name, value, script_path, ignore_list):
        return True
    return False


def generate_heap(frame, script_path, ignore, return_value = None):
    heap = Heap(script_path)
    while True:
        for variable_name in frame.f_locals:
            if should_ignore_on_stack(variable_name, frame.f_locals[variable_name], script_path, ignore):
                continue
            if primitive_type(type(frame.f_locals[variable_name])) != "ref":
                continue
            value = frame.f_locals[variable_name]
            heap.store(id(value), value)

        if return_value is not None:
            # Store return value
            if not should_ignore_on_stack("return", return_value, script_path) and not primitive_type(type(return_value)) != "ref":
                heap.store(id(return_value), return_value)

        frame = frame.f_back
        if frame is None or frame.f_code.co_qualname == "Bdb.run":
            break

    return heap


class ShownClassDefs:
    def __init__(self):
        self.frames = []

    def did_show(self, filename, line):
        return (filename, line) in self.frames[-1]

    def append(self, filename, line):
        self.frames[-1].append((filename, line))

    def push_frame(self):
        self.frames.append([])

    def pop_frame(self):
        self.frames.pop()


class PyTraceGenerator(bdb.Bdb):
    def __init__(self, trace_socket):
        super().__init__()
        self.trace_socket = trace_socket
        self.stack = Stack()
        self.stack_ignore = []
        self.init = False
        self.filename = ""
        self.skip_until = None
        self.import_following = False
        self.last_step_was_class = False
        self.prev_num_frames = 0
        self.shown_class_defs = ShownClassDefs()
        self.accumulated_stdout = ""
        self.captured_stdout = io.StringIO()
        self.last_event = ""

    def trace_dispatch(self, frame, event, arg):
        filename = frame.f_code.co_filename

        # Skip built-in modules
        # This might not be the best solution. Adjust if required.
        skip = False
        if self.skip_until is not None:
            skip = filename != self.skip_until
        elif not filename.startswith(os.path.dirname(self.filename)):
            skip = True
            self.skip_until = frame.f_back.f_code.co_filename
        if skip:
            return self.trace_dispatch
        else:
            self.skip_until = None

        line = frame.f_lineno
        if not self.init:
            self.init = True
            for variable_name in frame.f_locals:
                self.stack_ignore.append(variable_name)
        elif self.import_following:
            # Ignore new variables introduced through import
            for variable_name in frame.f_locals:
                if should_ignore_on_stack(variable_name, frame.f_locals[variable_name], self.filename, self.stack_ignore):
                    continue
                if not self.stack.contains(variable_name):
                    self.stack_ignore.append(variable_name)

        # Check if the next line will be an import
        next_source_line = linecache.getline(filename, line).strip()
        self.import_following = import_regex.search(next_source_line) is not None

        display_return = event == "return" and self.last_event != "exception" and len(self.stack.frames) > 1
        display_exception = event == "exception" and self.last_event != "return"
        if event == "line" or display_return or display_exception:
            for variable_name in frame.f_locals:
                if should_ignore_on_stack(variable_name, frame.f_locals[variable_name], self.filename, self.stack_ignore):
                    continue
                self.stack.push(variable_name, frame.f_locals[variable_name])
            if event == "return" and display_return:
                self.stack.push("return", arg)
                heap = generate_heap(frame, self.filename, self.stack_ignore, return_value=arg)
            else:
                heap = generate_heap(frame, self.filename, self.stack_ignore)
            accumulated_stdout = self.accumulated_stdout + self.captured_stdout.getvalue()

            traceback_text = None
            if event == "exception":
                exception_value = arg[1]
                traceback_text_tmp = io.StringIO()
                traceback.print_exception(exception_value, limit=0, file=traceback_text_tmp)
                traceback_text = traceback_text_tmp.getvalue()


            step = TraceStep(line, filename, copy.deepcopy(self.stack), copy.deepcopy(heap), accumulated_stdout, traceback_text)

            is_annotation = next_source_line.startswith("@")
            should_display_step = not is_annotation
            is_class_def = next_source_line.startswith("class ")
            class_def_already_shown = is_class_def and self.shown_class_defs.did_show(filename, line)
            should_display_step = should_display_step and not class_def_already_shown
            num_frames = len(self.stack.frames)
            is_inside_class_def = num_frames > self.prev_num_frames and self.last_step_was_class
            should_display_step = should_display_step and not is_inside_class_def
            if should_display_step:
                # Output trace
                if self.trace_socket is not None:
                    json_str = json.dumps(step.format()).encode('utf-8')
                    json_len = len(json_str).to_bytes(4, byteorder='big', signed=False)
                    self.trace_socket.sendall(json_len)
                    self.trace_socket.sendall(json_str)
                self.accumulated_stdout = accumulated_stdout
                self.clear_stdout_capture()
                if is_class_def:
                    self.shown_class_defs.append(filename, line)
                self.last_step_was_class = is_class_def
                self.prev_num_frames = num_frames

            if event == "exception":
                # Terminate visualization after first exception in user code
                self.set_quit()
        if event == "call":
            self.stack.push_frame(frame)
            self.shown_class_defs.push_frame()
        elif event == "return":
            self.stack.pop_frame()
            self.shown_class_defs.pop_frame()

        self.last_event = event

        return self.trace_dispatch

    def clear_stdout_capture(self):
        self.captured_stdout.close()
        self.captured_stdout = io.StringIO()
        sys.stdout = self.captured_stdout

    def run_script(self, filename, script_str):
        self.filename = filename
        code = compile(script_str, self.filename, "exec")
        real_stdout = sys.stdout
        sys.stdout = self.captured_stdout
        self.run(code)
        sys.stdout = real_stdout


if len(sys.argv) <= 1:
    eprint("not enough arguments")
    eprint("usage: python main.py file.py [port]")
    exit(1)

filename = os.path.abspath(sys.argv[1])
with open(filename, "r", encoding="utf-8") as f:
    script_str = f.read()

# Add a 'pass' at the end to also get the last trace step
# It's a bit hacky but probably the easiest solution
script_str += "\npass\n"

# Add script directory to path
sys.path.insert(0, os.path.dirname(filename))

trace_socket = None
try:
    if len(sys.argv) > 2:
        trace_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        trace_socket.connect(("127.0.0.1", int(sys.argv[2])))
except:
    trace_socket = None

debugger = PyTraceGenerator(trace_socket)
debugger.run_script(filename, script_str)

if trace_socket is not None:
    trace_socket.close()

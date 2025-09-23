import os
import sys

LIB_DIR = os.path.dirname(__file__)
INSTALLED_MODULE_NAME = 'wypp'

__wypp_runYourProgram = 1

def die(ecode: str | int | None = 1):
    if isinstance(ecode, str):
        sys.stderr.write(ecode)
        sys.stderr.write('\n')
        ecode = 1
    elif ecode == None:
        ecode = 0
    if sys.flags.interactive:
        os._exit(ecode)
    else:
        sys.exit(ecode)

def readFile(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path) as f:
            return f.read()

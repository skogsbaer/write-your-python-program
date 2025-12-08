from pathlib import Path
from fileTestsLib import *
import sys
import os

def pythonMinVersion(major: int, minor: int) -> bool:
    return sys.version_info >= (major, minor)

def pythonMaxVersion(major: int, minor: int) -> bool:
    return sys.version_info <= (major, minor)

directories = [Path("file-test-data/basics"),
               Path("file-test-data/extras")]

special = {
    'file-test-data/basics/recursive_ok.py': pythonMinVersion(3, 14),
    'file-test-data/basics/recursive_old_fail.py': pythonMaxVersion(3, 13)
    }

#directories = [Path("file-test-data/basics")]
#directories = [Path("file-test-data/extras")]

def main():
    for d in directories:
        for file in d.iterdir():
            if file.is_file():
                name = file.as_posix()
                if name.endswith('.py'):
                    if name in special:
                        if special[name]:
                            check(name)
                    else:
                        check(name)

    globalCtx.results.finish()

def extraChecks():
    # The localTyping file does not exist, running should thus fail
    localTyping = 'file-test-data/basics/typing.py'
    if os.path.exists(localTyping):
        raise ValueError(f'File {localTyping} should not exist')
    check(localTyping, exitCode=1)

try:
    main()
    extraChecks()
except KeyboardInterrupt:
    pass

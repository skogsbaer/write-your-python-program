from pathlib import Path
from fileTestsLib import *

directories = [Path("test-data-2.0/basics"), Path("test-data-2.0/extras")]

for d in directories:
    for file in d.iterdir():
        if file.is_file():
            name = file.as_posix()
            if name.endswith('.py'):
                check(name)

globalCtx.results.finish()

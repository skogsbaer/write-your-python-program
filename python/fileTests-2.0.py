from pathlib import Path
from fileTestsLib import *

directories = [Path("test-data-2.0/basics"),
               Path("test-data-2.0/extras"),
               Path("test-data-2.0/failing")]

#directories = [Path("test-data-2.0/basics")]
#directories = [Path("test-data-2.0/extras")]
#directories = [Path("test-data-2.0/failing")]

for d in directories:
    for file in d.iterdir():
        if file.is_file():
            name = file.as_posix()
            if name.endswith('.py'):
                check(name)

globalCtx.results.finish()

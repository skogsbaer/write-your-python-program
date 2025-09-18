from pathlib import Path
from fileTestsLib import *

directory = Path("test-data-2.0")

for file in directory.iterdir():
    if file.is_file():
        name = file.as_posix()
        if name.endswith('.py'):
            checkBasic(name)

globalCtx.results.finish()

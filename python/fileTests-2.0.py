from pathlib import Path
from fileTestsLib import *

directory = Path("test-data-2.0")

for file in directory.iterdir():
    if file.is_file():
        checkBasic(file.as_posix())

globalCtx.results.finish()

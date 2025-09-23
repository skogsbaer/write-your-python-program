from pathlib import Path
from fileTestsLib import *

directories = [Path("file-test-data/basics"),
               Path("file-test-data/extras")]

#directories = [Path("file-test-data/basics")]
#directories = [Path("file-test-data/extras")]

checkInstall('file-test-data/imports/fileWithImport.py')
checkInstall('file-test-data/imports/fileWithoutImport.py')
checkInstall('file-test-data/imports/fileWithBothImports.py')

for d in directories:
    for file in d.iterdir():
        if file.is_file():
            name = file.as_posix()
            if name.endswith('.py'):
                check(name)

globalCtx.results.finish()

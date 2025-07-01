from __future__ import annotations
import sys
import os
import instrument
import typecheck
import runner as r
import os
import runpy

def main(globals, argList=None):
    print('runner3')
    (args, restArgs) = r.parseCmdlineArgs(argList)
    fileToRun = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
        fileToRun = os.path.basename(fileToRun)
    modDir = os.path.dirname(fileToRun)
    instrument.setupFinder(modDir)
    sys.path.insert(0, modDir)
    modName = os.path.basename(os.path.splitext(fileToRun)[0])
    globals['wrapTypecheck'] = typecheck.wrapTypecheck
    print(f'Running module {modName}, file={fileToRun}')
    sys.dont_write_bytecode = True
    runpy.run_module(modName, init_globals=globals, run_name=modName)

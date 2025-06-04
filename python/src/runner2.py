import os
import sys
import runner as r
import importlib
import runpy
LIB_DIR = os.path.dirname(__file__)
TYPEGUARD_DIR = os.path.join(LIB_DIR, "..", "deps", "typeguard", "src")
sys.path.insert(0, TYPEGUARD_DIR)

import typeguard

def main(globals, argList=None):
    (args, restArgs) = r.parseCmdlineArgs(argList)
    typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS
    with typeguard.install_import_hook():
        typeguard.config.debug_instrumentation = True
        fileToRun = args.file
        if args.changeDir:
            os.chdir(os.path.dirname(fileToRun))
            fileToRun = os.path.basename(fileToRun)
        modDir = os.path.dirname(fileToRun)
        sys.path.insert(0, modDir)
        modName = os.path.basename(os.path.splitext(fileToRun)[0])
        print('here')
        # runpy.run_path(fileToRun, init_globals=globals, run_name=modName)
        # __import__(modName)
        importlib.import_module(modName)
        # import iterator

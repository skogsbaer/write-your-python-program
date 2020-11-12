import sys
import os

pythonVersion = sys.version.split()[0]
if not pythonVersion.startswith('3.'):
    sys.stderr.write("\nFEHLER: es wird Python 3 benoetigt, nicht " + pythonVersion + ".\n\n")
    os._exit(0)

import os.path
import runpy
import argparse
import json
import traceback
import shutil
import site
import importlib

LIB_DIR = os.path.dirname(__file__)
MODULES_TO_INSTALL = ['writeYourProgram.py', 'deepEq.py', 'drawingLib.py', '__init__.py']

def parseCmdlineArgs():
    parser = argparse.ArgumentParser(description='Run Your Program!')
    parser.add_argument('file', metavar='FILE',
                        help='The file to run')
    parser.add_argument('--check-runnable', dest='checkRunnable', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if loading the file raises errors')
    parser.add_argument('--check', dest='check', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if there are test errors.')
    parser.add_argument('--test-file', dest='testFile',
                        type=str, help='Run additional tests contained in this file.')
    try:
        args = parser.parse_args()
    except SystemExit as ex:
        os._exit(ex.code)
    if not args.file.endswith('.py'):
        print("FEHLER: die angegebene Datei ist keine Python Datei.")
        os._exit(0)
    return args

def readVersion():
    version = None
    try:
        with open(os.path.join(LIB_DIR, '..', '..', 'package.json')) as file:
            content = file.read()
            d = json.loads(content)
            version = d['version']
    except:
        pass
    return version

def printWelcomeString(file, version):
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else f'Version {version}, '
    print(f'=== WILLKOMMEN zu "Schreibe Dein Programm!" ' +
          f'({versionStr}Python {pythonVersion}, {file}) ===')

def installLib():
    userDir = site.USER_SITE
    try:
        os.makedirs(userDir)
        for f in os.listdir(userDir):
            p = os.path.join(userDir, f)
            if os.path.isfile(p):
                os.remove(p)
        d = os.path.join(userDir, 'wypp')
        for m in MODULES_TO_INSTALL:
            src = os.path.join(LIB_DIR, m)
            tgt = os.path.join(userDir, m)
            shutil.copyFile(src, tgt)
    except Exception as e:
        print(f'Installation of python files failed: {e}')

class Lib:
    def __init__(self, mod, isDict):
        if isDict:
            self.initModule = mod['initModule']
            self.resetTestCount = mod['resetTestCount']
            self.printTestResults = mod['printTestResults']
        else:
            self.initModule = mod.initModule
            self.resetTestCount = mod.resetTestCount
            self.printTestResults = mod.printTestResults

def loadLib(onlyCheckRunnable):
    libDefs = None
    try:
        wypp = importlib.import_module('wypp')
        libDefs = Lib(wypp, False)
    except:
        pass
    if not libDefs:
        libFile = os.path.join(LIB_DIR, 'writeYourProgram.py')
        libDefs = runpy.run_path(libFile)
    libDefs.initModule(enableChecks=not onlyCheckRunnable,
                       quiet=onlyCheckRunnable)
    return libDefs

def runCode(fileToRun, libDefs, onlyCheckRunnable):
    doRun = lambda: runpy.run_path(fileToRun, libDefs)
    if onlyCheckRunnable:
        try:
            doRun()
        except Exception as e:
            print(f'Loading file {fileToRun} crashed')
            traceback.print_exc()
            os._exit(1)
        else:
            os._exit(0)
    userDefs = doRun()
    return userDefs

def runTestsInFile(testFile, libDefs):
    allDefs = {}
    for k, v in libDefs.items():
        allDefs[k] = v
    for k, v in userDefs.items():
        allDefs[k] = v
    libDefs.resetTestCount()
    runpy.run_path(testFile, allDefs)
    return libDefs['printTestResults']('Dozent:  ')

def performChecks(check, testFile, libDefs):
    prefix = ''
    if check and testFile:
        prefix = 'Student: '
    testResultsStudent = libDefs.printTestResults(prefix)
    if check:
        testResultsInstr = {'total': 0, 'failing': 0}
        if testFile:
            testResultsInstr = runTestsInFile(args.testFile, libDefs)
        failingSum = testResultsStudent['failing'] + testResultsInstr['failing']
        os._exit(0 if failingSum < 1 else 1)

def prepareInteractive():
    print('\n')
    # clear the terminal, reset on Mac OSX and Linux. This prevents strange history bugs where
    # the command just entered is echoed again (2020-10-14).
    os.system('cls' if os.name == 'nt' else 'reset')

def enterInteractive():
    for k, v in userDefs.items():
        globals()[k] = v
    print()

def main():
    args = parseCmdlineArgs()
    fileToRun = args.file
    isInteractive = sys.flags.interactive
    version = readVersion()
    if isInteractive:
        prepareInteractive()
    installLib()
    if not args.checkRunnable:
        printWelcomeString(fileToRun, version)
    libDefs = loadLib(onlyCheckRunnable=args.checkRunnable)
    userDefs = runCode(fileToRun, libDefs, args.checkRunnable)
    performChecks(args.check, args.testFile, libDefs)
    if isInteractive:
        enterInteractive()

if __name__ == '__main__':
    main()

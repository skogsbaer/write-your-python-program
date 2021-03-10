from __future__ import annotations as anns
import sys
import os
import os.path
import argparse
import json
import traceback
import shutil
import site
import importlib
import re

__wypp_runYourProgram = 1

def die(ecode=1):
    if sys.flags.interactive:
        os._exit(ecode)
    else:
        sys.exit(ecode)

# Simulates that wypp cannot be imported so that we can test the code path where
# wypp is directly loaded from the writeYourProgram.py file. The default is False.
SIMULATE_LIB_FROM_FILE = False
ASSERT_INSTALL = False # if True, then a failing installation causes a total failure
VERBOSE = False # set via commandline
LIB_DIR = os.path.dirname(__file__)

INSTALLED_MODULE_NAME = 'wypp'
MODULES_TO_INSTALL = ['writeYourProgram.py', 'drawingLib.py', '__init__.py']

def verbose(s):
    if VERBOSE:
        print('[V] ' + s)

def parseCmdlineArgs():
    parser = argparse.ArgumentParser(description='Run Your Program!')
    parser.add_argument('file', metavar='FILE',
                        help='The file to run', nargs='?')
    parser.add_argument('--check-runnable', dest='checkRunnable', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if loading the file raises errors')
    parser.add_argument('--check', dest='check', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if there are test errors.')
    parser.add_argument('--install-mode', dest='installMode', type=str,
                        help='One of "regular", "assertInstall", "libFromFile"')
    parser.add_argument('--verbose', dest='verbose', action='store_const',
                        const=True, default=False,
                        help='Be verbose')
    parser.add_argument('--quiet', dest='quiet', action='store_const',
                        const=True, default=False, help='Be extra quiet')
    parser.add_argument('--no-install', dest='noInstall', action='store_const',
                        const=True, default=False, help='Do not install the wypp files')
    parser.add_argument('--no-clear', dest='noClear', action='store_const',
                        const=True, default=False, help='Do not clear the terminal')
    parser.add_argument('--test-file', dest='testFile',
                        type=str, help='Run additional tests contained in this file.')
    parser.add_argument('--change-directory', dest='changeDir', action='store_const',
                        const=True, default=False,
                        help='Change to the directory of FILE before running')
    try:
        args, restArgs = parser.parse_known_args()
    except SystemExit as ex:
        die(ex.code)
    if args.file and not args.file.endswith('.py'):
        print("FEHLER: die angegebene Datei ist keine Python Datei.")
        die()
    return (args, restArgs)

def readFile(f):
    with open(f) as file:
        return file.read()

def readVersion():
    version = None
    try:
        content = readFile(os.path.join(LIB_DIR, '..', '..', 'package.json'))
        d = json.loads(content)
        version = d['version']
    except:
        pass
    return version

def printWelcomeString(file, version):
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else 'Version %s, ' % version
    pythonVersion = sys.version.split()[0]
    print('=== WILLKOMMEN zu "Schreibe Dein Programm!" ' +
          '(%sPython %s, %s) ===' % (versionStr, pythonVersion, file))

def isSameFile(f1, f2):
    x = readFile(f1)
    y = readFile(f2)
    return x == y

def installLib():
    userDir = site.USER_SITE
    installDir = os.path.join(userDir, INSTALLED_MODULE_NAME)
    try:
        os.makedirs(installDir, exist_ok=True)
        installedFiles = sorted([f for f in os.listdir(installDir)
                                   if os.path.isfile(os.path.join(installDir, f))])
        wantedFiles = sorted(MODULES_TO_INSTALL)
        if installedFiles == wantedFiles:
            for i in range(len(installedFiles)):
                f1 = os.path.join(installDir, installedFiles[i])
                f2 = os.path.join(LIB_DIR, wantedFiles[i])
                if not isSameFile(f1, f2):
                    break
            else:
                # no break, all files equal
                verbose('All wypp files already installed in ' + userDir)
                return
        for f in installedFiles:
            p = os.path.join(installDir, f)
            os.remove(p)
        d = os.path.join(installDir, 'wypp')
        for m in MODULES_TO_INSTALL:
            src = os.path.join(LIB_DIR, m)
            tgt = os.path.join(installDir, m)
            shutil.copyfile(src, tgt)
        print('Die Python-Bibliothek wurde erfolgreich in ' + userDir + ' installiert.\n' +
              'Bitte starten Sie Visual Studio Code neu, um sicherzustellen, dass überall\n' +
              'die neueste Version verwendet wird.\n')
    except Exception as e:
        print('Die Installation der Python-Bibliothek ist fehlgeschlagen: ' + str(e))
        if ASSERT_INSTALL:
            raise e

class Lib:
    def __init__(self, mod, properlyImported):
        self.properlyImported = properlyImported
        if not properlyImported:
            self.initModule = mod['initModule']
            self.resetTestCount = mod['resetTestCount']
            self.printTestResults = mod['printTestResults']
            self.dict = mod
        else:
            self.initModule = mod.initModule
            self.resetTestCount = mod.resetTestCount
            self.printTestResults = mod.printTestResults
            d = {}
            self.dict = d
            for name in dir(mod):
                if name and name[0] != '_':
                  d[name] = getattr(mod, name)

def loadLib(onlyCheckRunnable):
    libDefs = None
    mod = INSTALLED_MODULE_NAME
    verbose('Attempting to import ' + mod)
    try:
        if SIMULATE_LIB_FROM_FILE:
            raise ImportError('deliberately failing when importing ' + mod)
        # It's the prefered way to properly import wypp. With this setup, student's code
        # may or may not import wypp. And if it does import wypp, there is no suffering from
        # module schizophrenia.
        wypp = importlib.import_module(mod)
        libDefs = Lib(wypp, True)
        verbose('Successfully imported module ' + mod)
    except Exception as e:
        verbose('Failed to import %s: %s' % (mod, e))
        pass
    if not libDefs:
        # This code path is only here to support the case that installation fails.
        libFile = os.path.join(LIB_DIR, 'writeYourProgram.py')
        d = {}
        runCode(libFile, d, [])
        verbose('Successfully loaded library code from ' + libFile)
        libDefs = Lib(d, False)
    libDefs.initModule(enableChecks=not onlyCheckRunnable,
                       quiet=onlyCheckRunnable)
    return libDefs

importRe = importRe = re.compile(r'^import\s+wypp\s*$|^from\s+wypp\s+import\s+\*\s*$')

def findWyppImport(fileName):
    lines = []
    try:
        with open(fileName) as f:
            lines = f.readlines()
    except Exception as e:
        verbose('Failed to read code from %s: %s' % (fileName, e))
    for l in lines:
        if importRe.match(l):
            return True
    return False

def runCode(fileToRun, globals, args):
    with open(fileToRun) as f:
        flags = 0 | anns.compiler_flag
        code = compile(f.read(), fileToRun, 'exec', flags=flags, dont_inherit=True)
        oldArgs = sys.argv
        try:
            sys.argv = [fileToRun] + args
            exec(code, globals)
        finally:
            sys.argv = oldArgs

def runStudentCode(fileToRun, globals, libDefs, onlyCheckRunnable, args):
    importsWypp = findWyppImport(fileToRun)
    if importsWypp:
        if not libDefs.properlyImported:
            globals[INSTALLED_MODULE_NAME] = libDefs.dict
    else:
        # This case will go away once we required students to import wypp explicitly
        globals.update(libDefs.dict)
    localDir = os.path.dirname(fileToRun)
    if localDir not in sys.path:
        sys.path.insert(0, localDir)
    doRun = lambda: runCode(fileToRun, globals, args)
    if onlyCheckRunnable:
        try:
            doRun()
        except Exception as e:
            print('Loading file %s crashed' % fileToRun)
            traceback.print_exc()
            die()
        else:
            die(0)
    doRun()

# globals already contain libDefs
def runTestsInFile(testFile, globals, libDefs):
    libDefs.resetTestCount()
    runCode(testFile, globals, [])
    return libDefs.dict['printTestResults']('Dozent:  ')

# globals already contain libDefs
def performChecks(check, testFile, globals, libDefs):
    prefix = ''
    if check and testFile:
        prefix = 'Student: '
    testResultsStudent = libDefs.printTestResults(prefix)
    if check:
        testResultsInstr = {'total': 0, 'failing': 0}
        if testFile:
            testResultsInstr = runTestsInFile(testFile, globals, libDefs)
        failingSum = testResultsStudent['failing'] + testResultsInstr['failing']
        die(0 if failingSum < 1 else 1)

def prepareInteractive(reset=True):
    print('\n')
    # clear the terminal, reset on Mac OSX and Linux. This prevents strange history bugs where
    # the command just entered is echoed again (2020-10-14).
    if reset:
        os.system('cls' if os.name == 'nt' else 'reset')

def enterInteractive(userDefs):
    for k, v in userDefs.items():
        globals()[k] = v
    print()

def isMyCode(frame):
    return '__wypp_runYourProgram' in frame.f_globals

def ignoreFrame(frame):
    return isMyCode(frame)

def limitTraceback(fullTb):
    tb = fullTb
    while tb:
        if not ignoreFrame(tb.tb_frame):
            verbose('Stopping at first non-ignorable frame ' + str(tb.tb_frame))
            return tb
        verbose('Ignoring frame ' + str(tb.tb_frame))
        tb = tb.tb_next
    verbose('I would ignore all frames, so I return None')
    return None

def main(globals):
    (args, restArgs) = parseCmdlineArgs()
    global VERBOSE, SIMULATE_LIB_FROM_FILE, ASSERT_INSTALL
    if args.verbose:
        VERBOSE = True
    if args.installMode == 'regular' or args.installMode is None:
        pass
    elif args.installMode == 'libFromFile':
        SIMULATE_LIB_FROM_FILE = True
    elif args.installMode == 'assertInstall':
        ASSERT_INSTALL = True
    else:
        print('Invalid value for --install-mode: %s' % args.installMode)
        sys.exit(1)
    fileToRun = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
    isInteractive = sys.flags.interactive
    version = readVersion()
    if isInteractive:
        prepareInteractive(reset=not args.noClear)
    if not args.noInstall:
        installLib()
    if fileToRun is None:
        return
    if not args.checkRunnable and not args.quiet:
        printWelcomeString(fileToRun, version)
    libDefs = loadLib(onlyCheckRunnable=args.checkRunnable)
    try:
        runStudentCode(fileToRun, globals, libDefs, args.checkRunnable, restArgs)
    except:
        (etype, val, tb) = sys.exc_info()
        limitedTb = limitTraceback(tb)
        sys.stderr.write('\n')
        traceback.print_exception(etype, val, limitedTb, file=sys.stderr)
        die(1)
    performChecks(args.check, args.testFile, globals, libDefs)
    if isInteractive:
        enterInteractive(globals)

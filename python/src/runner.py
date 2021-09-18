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
untypyPath = os.path.join(os.path.dirname(__file__), "..", "deps", "untypy")
if untypyPath not in sys.path:
    sys.path.insert(1, untypyPath)
import untypy
import code
import ast
from modulefinder import ModuleFinder

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

def printStderr(s=''):
    sys.stderr.write(s + '\n')

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
    parser.add_argument('--interactive', dest='interactive', action='store_const',
                        const=True, default=False,
                        help='Run REPL after the programm has finished')
    parser.add_argument('--no-typechecking', dest='checkTypes', action='store_const',
                        const=False, default=True,
                        help='Do not check type annotations')
    try:
        args, restArgs = parser.parse_known_args()
    except SystemExit as ex:
        die(ex.code)
    if args.file and not args.file.endswith('.py'):
        printStderr("FEHLER: die angegebene Datei ist keine Python Datei.")
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
    printStderr('=== WILLKOMMEN zu "Schreibe Dein Programm!" ' +
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
        printStderr('Die Python-Bibliothek wurde erfolgreich in ' + userDir + ' installiert.\n' +
                    'Bitte starten Sie Visual Studio Code neu, um sicherzustellen, dass überall\n' +
                    'die neueste Version verwendet wird.\n')
    except Exception as e:
        printStderr('Die Installation der Python-Bibliothek ist fehlgeschlagen: ' + str(e))
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

def findImportedModules(path, file):
    finder = ModuleFinder(path=path)
    try:
        finder.run_script(file)
    except:
        return []
    res = []
    for name, mod in finder.modules.items():
        if name != '__main__' and mod.__file__ and not os.path.isabs(mod.__file__):
            res.append(name)
    return res

class sysPathPrepended:
    def __init__(self, d):
        self.dir = d
        self.inserted = False
    def __enter__(self):
        if self.dir not in sys.path:
            sys.path.insert(0, self.dir)
            self.inserted = True
    def __exit__(self, exc_type, value, traceback):
        if self.inserted:
            sys.path.remove(self.dir)
            self.inserted = False

def runCode(fileToRun, globals, args, *, useUntypy=True):
    localDir = os.path.dirname(fileToRun)
    with sysPathPrepended(localDir):
        with open(fileToRun) as f:
            flags = 0 | anns.compiler_flag
            codeTxt = f.read()
            if useUntypy:
                verbose(f'finding modules imported by {fileToRun}')
                importedMods = findImportedModules([localDir], fileToRun)
                verbose('finished finding modules, now installing import hook on ' + repr(importedMods))
                untypy.just_install_hook(importedMods)
                verbose(f"transforming {fileToRun} for typechecking")
                tree = compile(codeTxt, fileToRun, 'exec', flags=(flags | ast.PyCF_ONLY_AST),
                               dont_inherit=True, optimize=-1)
                untypy.transform_tree(tree)
                verbose(f'done with transformation of {fileToRun}')
                code = tree
            else:
                code = codeTxt
            compiledCode = compile(code, fileToRun, 'exec', flags=flags, dont_inherit=True)
            oldArgs = sys.argv
            try:
                sys.argv = [fileToRun] + args
                exec(compiledCode, globals)
            finally:
                sys.argv = oldArgs

def runStudentCode(fileToRun, globals, libDefs, onlyCheckRunnable, args, *, useUntypy=True):
    importsWypp = findWyppImport(fileToRun)
    if importsWypp:
        if not libDefs.properlyImported:
            globals[INSTALLED_MODULE_NAME] = libDefs.dict
    doRun = lambda: runCode(fileToRun, globals, args, useUntypy=useUntypy)
    if onlyCheckRunnable:
        try:
            doRun()
        except:
            printStderr('Loading file %s crashed' % fileToRun)
            handleCurrentException()
        else:
            die(0)
    doRun()

# globals already contain libDefs
def runTestsInFile(testFile, globals, libDefs, useUntypy=True):
    printStderr()
    printStderr(f"Running tutor's tests in {testFile}")
    libDefs.resetTestCount()
    try:
        runCode(testFile, globals, [], useUntypy=useUntypy)
    except:
        handleCurrentException()
    return libDefs.dict['printTestResults']('Tutor:  ')

# globals already contain libDefs
def performChecks(check, testFile, globals, libDefs, useUntypy=True):
    prefix = ''
    if check and testFile:
        prefix = 'Student: '
    testResultsStudent = libDefs.printTestResults(prefix)
    if check:
        testResultsInstr = {'total': 0, 'failing': 0}
        if testFile:
            testResultsInstr = runTestsInFile(testFile, globals, libDefs, useUntypy=useUntypy)
        failingSum = testResultsStudent['failing'] + testResultsInstr['failing']
        die(0 if failingSum < 1 else 1)

def prepareInteractive(reset=True):
    print()
    if reset:
        if os.name == 'nt':
            # clear the terminal
            os.system('cls')
        else:
            # On linux & mac use ANSI Sequence for this
            print('\033[2J\033[H')

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

def handleCurrentException(exit=True, removeFirstTb=False, file=sys.stderr):
    (etype, val, tb) = sys.exc_info()
    if isinstance(val, untypy.error.UntypyTypeError) or isinstance(val, untypy.error.UntypyAttributeError):
        file.write(str(val))
        file.write('\n')
    else:
        if tb and removeFirstTb:
            tb = tb.tb_next
        limitedTb = limitTraceback(tb)
        file.write('\n')
        traceback.print_exception(etype, val, limitedTb, file=file)
    if exit:
        die(1)

HISTORY_SIZE = 1000

def getHistoryFilePath():
    envVar = 'HOME'
    if os.name == 'nt':
        envVar = 'USERPROFILE'
    d = os.getenv(envVar, None)
    if d:
        return os.path.join(d, ".wypp_history")
    else:
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
        printStderr('Invalid value for --install-mode: %s' % args.installMode)
        sys.exit(1)
    fileToRun = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
    isInteractive = args.interactive
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

    globals['__name__'] = '__wypp__'
    sys.modules['__wypp__'] = sys.modules['__main__']
    try:
        verbose(f'running code in {fileToRun}')
        runStudentCode(fileToRun, globals, libDefs, args.checkRunnable, restArgs,
                       useUntypy=args.checkTypes)
    except:
        handleCurrentException()

    performChecks(args.check, args.testFile, globals, libDefs, useUntypy=args.checkTypes)

    if isInteractive:
        enterInteractive(globals)
        if args.checkTypes:
            consoleClass = TypecheckedInteractiveConsole
        else:
            consoleClass = code.InteractiveConsole
        historyFile = getHistoryFilePath()
        try:
            import readline
            readline.parse_and_bind('tab: complete')
            if historyFile and os.path.exists(historyFile):
                readline.read_history_file(historyFile)
        except:
            pass
        try:
            consoleClass(locals=globals).interact(banner="", exitmsg='')
        finally:
            if readline and historyFile:
                readline.set_history_length(HISTORY_SIZE)
                readline.write_history_file(historyFile)

class TypecheckedInteractiveConsole(code.InteractiveConsole):

    def showtraceback(self) -> None:
        handleCurrentException(exit=False, removeFirstTb=True, file=sys.stdout)

    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False
        if code is None:
            return True
        try:
            ast = untypy.just_transform("\n".join(self.buffer), filename, symbol)
            code = compile(ast, filename, symbol)
        except Exception as e:
            if e.text == "":
                pass
            else:
                traceback.print_tb(e.__traceback__)
        self.runcode(code)
        return False

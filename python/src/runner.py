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
import code
import ast
from modulefinder import ModuleFinder
from pathlib import Path

__wypp_runYourProgram = 1

def die(ecode=1):
    if sys.flags.interactive:
        os._exit(ecode)
    else:
        sys.exit(ecode)

def getEnv(name, conv, default):
    s = os.getenv(name)
    if s is None:
        return default
    try:
        return conv(s)
    except:
        return default

VERBOSE = False # set via commandline
DEBUG = getEnv("WYPP_DEBUG", bool, False)

def enableVerbose():
    global VERBOSE
    VERBOSE = True

LIB_DIR = os.path.dirname(__file__)
INSTALLED_MODULE_NAME = 'wypp'
FILES_TO_INSTALL = ['writeYourProgram.py', 'drawingLib.py', '__init__.py']

UNTYPY_DIR = os.path.join(LIB_DIR, "..", "deps", "untypy", "untypy")
UNTYPY_MODULE_NAME = 'untypy'

def verbose(s):
    if VERBOSE or DEBUG:
        printStderr('[V] ' + s)

def printStderr(s=''):
    sys.stderr.write(s + '\n')

class InstallMode:
    dontInstall = 'dontInstall'
    installOnly = 'installOnly'
    install = 'install'
    assertInstall = 'assertInstall'
    allModes = [dontInstall, installOnly, install, assertInstall]

def parseCmdlineArgs(argList):
    parser = argparse.ArgumentParser(description='Run Your Program!',
                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--check-runnable', dest='checkRunnable', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if loading the file raises errors')
    parser.add_argument('--check', dest='check', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if there are test errors.')
    parser.add_argument('--install-mode', dest='installMode', type=str,
                        default=InstallMode.dontInstall,
                        help="""The install mode can be one of the following:
- dontInstall     do not install the wypp library (default)
- installOnly     install the wypp library and quit
- install         install the wypp library and continue even if installation fails
- assertInstall   check whether wypp is installed
""")
    parser.add_argument('--verbose', dest='verbose', action='store_const',
                        const=True, default=False,
                        help='Be verbose')
    parser.add_argument('--quiet', dest='quiet', action='store_const',
                        const=True, default=False, help='Be extra quiet')
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
    parser.add_argument('file', metavar='FILE',
                        help='The file to run', nargs='?')
    if argList is None:
        argList = sys.argv[1:]
    try:
        args, restArgs = parser.parse_known_args(argList)
    except SystemExit as ex:
        die(ex.code)
    if args.file and not args.file.endswith('.py'):
        printStderr(f'ERROR: file {args.file} is not a python file')
        die()
    if args.installMode not in InstallMode.allModes:
        printStderr(f'ERROR: invalid install mode {args.installMode}.')
        die()
    return (args, restArgs)

def readFile(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path) as f:
            return f.read()

def readVersion():
    version = None
    try:
        content = readFile(os.path.join(LIB_DIR, '..', '..', 'package.json'))
        d = json.loads(content)
        version = d['version']
    except:
        pass
    return version

def printWelcomeString(file, version, useUntypy):
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else 'Version %s, ' % version
    pythonVersion = sys.version.split()[0]
    tycheck = ''
    if not useUntypy:
        tycheck = ', no typechecking'
    printStderr('=== WELCOME to "Write Your Python Program" ' +
                '(%sPython %s, %s%s) ===' % (versionStr, pythonVersion, file, tycheck))

def isSameFile(f1, f2):
    x = readFile(f1)
    y = readFile(f2)
    return x == y

def installFromDir(srcDir, targetDir, mod, files=None):
    verbose(f'Installing from {srcDir} to {targetDir}/{mod}')
    if files is None:
        files = [p.relative_to(srcDir) for p in Path(srcDir).rglob('*.py')]
    else:
        files = [Path(f) for f in files]
    installDir = os.path.join(targetDir, mod)
    os.makedirs(installDir, exist_ok=True)
    installedFiles = sorted([p.relative_to(installDir) for p in Path(installDir).rglob('*.py')])
    wantedFiles = sorted(files)
    if installedFiles == wantedFiles:
        for i in range(len(installedFiles)):
            f1 = os.path.join(installDir, installedFiles[i])
            f2 = os.path.join(srcDir, wantedFiles[i])
            if not isSameFile(f1, f2):
                verbose(f'{f1} and {f2} differ')
                break
        else:
            # no break, all files equal
            verbose(f'All files from {srcDir} already installed in {targetDir}/{mod}')
            return True
    else:
        verbose(f'Installed files {installedFiles} and wanted files {wantedFiles} are different')
    for f in installedFiles:
        p = os.path.join(installDir, f)
        os.remove(p)
    d = os.path.join(installDir, mod)
    for f in wantedFiles:
        src = os.path.join(srcDir, f)
        tgt = os.path.join(installDir, f)
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        shutil.copyfile(src, tgt)
    verbose(f'Finished installation from {srcDir} to {targetDir}/{mod}')
    return False

def installLib(mode):
    verbose("installMode=" + mode)
    if mode == InstallMode.dontInstall:
        verbose("No installation of WYPP should be performed")
        return
    targetDir = os.getenv('WYPP_INSTALL_DIR', site.USER_SITE)
    try:
        allEq1 = installFromDir(LIB_DIR, targetDir, INSTALLED_MODULE_NAME, FILES_TO_INSTALL)
        allEq2 = installFromDir(UNTYPY_DIR, targetDir, UNTYPY_MODULE_NAME)
        if allEq1 and allEq2:
            verbose(f'WYPP library in {targetDir} already up to date')
            if mode == InstallMode.installOnly:
                printStderr(f'WYPP library in {targetDir} already up to date')
            return
        else:
            if mode == InstallMode.assertInstall:
                printStderr("The WYPP library was not installed before running this command.")
                die(1)
            printStderr(f'The WYPP library has been successfully installed in {targetDir}')
    except Exception as e:
        printStderr('Installation of the WYPP library failed: ' + str(e))
        if mode == InstallMode.installOnly:
            raise e
    if mode == InstallMode.installOnly:
        printStderr('Exiting after installation of the WYPP library')
        die(0)

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

def prepareLib(onlyCheckRunnable):
    libDefs = None
    mod = INSTALLED_MODULE_NAME
    verbose('Attempting to import ' + mod)
    wypp = importlib.import_module(mod)
    libDefs = Lib(wypp, True)
    verbose('Successfully imported module ' + mod)
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
    realdirs = [os.path.realpath(p) for p in path]
    res = []
    for name, mod in finder.modules.items():
        if name != '__main__' and mod.__file__:
            realp = os.path.realpath(mod.__file__)
            good = False
            for d in realdirs:
                if realp.startswith(d):
                    good = True
                    break
            if good:
                res.append(name)
    return res

class RunSetup:
    def __init__(self, sysPath):
        self.sysPath = sysPath
        self.sysPathInserted = False
    def __enter__(self):
        if self.sysPath not in sys.path:
            sys.path.insert(0, self.sysPath)
            self.sysPathInserted = True
    def __exit__(self, exc_type, value, traceback):
        if self.sysPathInserted:
            sys.path.remove(self.sysPath)
            self.sysPathInserted = False

def runCode(fileToRun, globals, args, useUntypy=True):
    localDir = os.path.dirname(fileToRun)

    with RunSetup(localDir):
        codeTxt = readFile(fileToRun)
        flags = 0 | anns.compiler_flag
        if useUntypy:
            verbose(f'finding modules imported by {fileToRun}')
            importedMods = findImportedModules([localDir], fileToRun)
            verbose('finished finding modules, now installing import hook on ' + repr(importedMods))
            untypy.just_install_hook(importedMods + ['__wypp__'])
            verbose(f"transforming {fileToRun} for typechecking")
            tree = compile(codeTxt, fileToRun, 'exec', flags=(flags | ast.PyCF_ONLY_AST),
                            dont_inherit=True, optimize=-1)
            untypy.transform_tree(tree, fileToRun)
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

def runStudentCode(fileToRun, globals, onlyCheckRunnable, args, useUntypy=True):
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

def tbToFrameList(tb):
    cur = tb
    res = []
    while cur:
        res.append(cur.tb_frame)
        cur = cur.tb_next
    return res

def ignoreFrame(frame):
    if DEBUG:
        return False
    modName = frame.f_globals["__name__"]
    return '__wypp_runYourProgram' in frame.f_globals or \
        modName == 'untypy' or modName.startswith('untypy.') or \
        modName == 'wypp' or modName.startswith('wypp.')

# Returns a StackSummary object
def limitTraceback(tb):
    frames = [(f, f.f_lineno) for f in tbToFrameList(tb) if not ignoreFrame(f)]
    return traceback.StackSummary.extract(frames)

def handleCurrentException(exit=True, removeFirstTb=False, file=sys.stderr):
    (etype, val, tb) = sys.exc_info()
    if tb and removeFirstTb:
        tb = tb.tb_next
    stackSummary = limitTraceback(tb)
    header = False
    for x in stackSummary.format():
        if not header:
            file.write('Traceback (most recent call last):\n')
            header = True
        file.write(x)
    if isinstance(val, untypy.error.UntypyError):
        name = 'Wypp' + val.simpleName()
        file.write(name)
        s = str(val)
        if s and s[0] != '\n':
            file.write(': ')
        file.write(s)
        file.write('\n')
    else:
        for x in traceback.format_exception_only(etype, val):
            file.write(x)
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

# We cannot import untypy at the top of the file because we might have to install it first.
def importUntypy():
    global untypy
    try:
        import untypy
    except ModuleNotFoundError as e:
        printStderr(f"Module untypy not found, sys.path={sys.path}: {e}")
        die(1)

def main(globals, argList=None):
    v = sys.version_info
    if v.major < 3 or v.minor < 9:
        vStr = sys.version.split()[0]
        print(f"""
Python in version 3.9 or newer is required. You are still using version {vStr}, please upgrade!
""")
        sys.exit(1)
    (args, restArgs) = parseCmdlineArgs(argList)
    global VERBOSE
    if args.verbose:
        VERBOSE = True

    installLib(args.installMode)
    if site.USER_SITE not in sys.path:
        if not site.ENABLE_USER_SITE:
            printStderr(f"User site-packages disabled ({site.USER_SITE}. This might cause problems importing wypp or untypy.")
        else:
            verbose(f"Adding user site-package directory {site.USER_SITE} to sys.path")
            sys.path.append(site.USER_SITE)
    importUntypy()

    fileToRun = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
        fileToRun = os.path.basename(fileToRun)

    isInteractive = args.interactive
    version = readVersion()
    if isInteractive:
        prepareInteractive(reset=not args.noClear)

    if fileToRun is None:
        return
    if not args.checkRunnable and not args.quiet:
        printWelcomeString(fileToRun, version, useUntypy=args.checkTypes)

    libDefs = prepareLib(onlyCheckRunnable=args.checkRunnable)

    globals['__name__'] = '__wypp__'
    sys.modules['__wypp__'] = sys.modules['__main__']
    try:
        verbose(f'running code in {fileToRun}')
        globals['__file__'] = fileToRun
        runStudentCode(fileToRun, globals, args.checkRunnable, restArgs,
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
            import ast
            tree = compile("\n".join(self.buffer), filename, symbol, flags=ast.PyCF_ONLY_AST, dont_inherit=True, optimize=-1)
            untypy.transform_tree(tree, filename)
            code = compile(tree, filename, symbol)
        except Exception as e:
            if hasattr(e, 'text') and e.text == "":
                pass
            else:
                traceback.print_tb(e.__traceback__)
        self.runcode(code)
        return False

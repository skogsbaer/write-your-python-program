# Step 2 of the runner. Assumes that typeguard has been installed

import sys
import os
import os.path
import json
import traceback
import site
import importlib
import re
import code
from modulefinder import ModuleFinder
import subprocess
import runpy
from dataclasses import dataclass

# local imports
from runnerCommon import *
import stacktrace
import i18n
import paths
import instrument
from myLogging import *
import errors

__wypp_runYourProgram = 1

def readGitVersion():
    thisDir = os.path.basename(LIB_DIR)
    baseDir = os.path.join(LIB_DIR, '..', '..')
    if thisDir == 'src' and os.path.isdir(os.path.join(baseDir, '.git')):
        try:
            h = subprocess.check_output(['git', '-C', baseDir, 'rev-parse', '--short', 'HEAD'],
                encoding='UTF-8').strip()
            changes = subprocess.check_output(
                    ['git', '-C', baseDir, 'status', '--porcelain', '--untracked-files=no'],
                    encoding='UTF-8').strip()
            if changes:
                return f'git-{h}-dirty'
            else:
                return f'git-{h}'
        except subprocess.CalledProcessError:
            return 'git-?'
    else:
        return None

def readVersion():
    version = readGitVersion()
    if version is not None:
        return version
    try:
        content = readFile(os.path.join(LIB_DIR, '..', '..', 'package.json'))
        d = json.loads(content)
        version = d['version']
    except:
        pass
    return version

def printWelcomeString(file, version, doTypecheck):
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else 'Version %s, ' % version
    pythonVersion = sys.version.split()[0]
    tycheck = ''
    if not doTypecheck:
        tycheck = ', no typechecking'
    printStderr('=== WELCOME to "Write Your Python Program" ' +
                '(%sPython %s, %s%s) ===' % (versionStr, pythonVersion, file, tycheck))


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

def prepareLib(onlyCheckRunnable, enableTypeChecking):
    libDefs = None
    mod = INSTALLED_MODULE_NAME
    verbose('Attempting to import ' + mod)
    wypp = importlib.import_module(mod)
    libDefs = Lib(wypp, True)
    verbose(f'Successfully imported module {mod} from file {wypp.__file__}')
    libDefs.initModule(enableChecks=not onlyCheckRunnable,
                       enableTypeChecking=enableTypeChecking,
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
        if name != '__main__' and (f := mod.__file__):    # type: ignore
            realp = os.path.realpath(f)
            good = False
            for d in realdirs:
                if realp.startswith(d):
                    good = True
                    break
            if good:
                res.append(name)
    return res

@dataclass
class RunSetup:
    def __init__(self, pathDir: str, args: list[str]):
        self.pathDir = pathDir
        self.args = args
        self.sysPathInserted = False
        self.oldArgs = sys.argv
    def __enter__(self):
        if self.pathDir not in sys.path:
            sys.path.insert(0, self.pathDir)
            self.sysPathInserted = True
        sys.argv = self.args
        self.originalProfile = sys.getprofile()
        stacktrace.installProfileHook()
    def __exit__(self, exc_type, value, traceback):
        sys.setprofile(self.originalProfile)
        if self.sysPathInserted:
            sys.path.remove(self.pathDir)
            self.sysPathInserted = False
        sys.argv = self.oldArgs

def runCode(fileToRun, globals, args, doTypecheck=True, extraDirs=None):
    if not extraDirs:
        extraDirs = []
    modDir = os.path.dirname(fileToRun)
    with RunSetup(modDir, [fileToRun] + args):
        with instrument.setupFinder(modDir, extraDirs, doTypecheck):
            modName = os.path.basename(os.path.splitext(fileToRun)[0])
            sys.dont_write_bytecode = True # FIXME: remove?
            runpy.run_module(modName, init_globals=globals, run_name='__wypp__', alter_sys=False)

def runStudentCode(fileToRun, globals, onlyCheckRunnable, args, doTypecheck=True, extraDirs=None):
    doRun = lambda: runCode(fileToRun, globals, args, doTypecheck=doTypecheck, extraDirs=extraDirs)
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
def runTestsInFile(testFile, globals, libDefs, doTypecheck=True, extraDirs=[]):
    printStderr()
    printStderr(f"Running tutor's tests in {testFile}")
    libDefs.resetTestCount()
    try:
        runCode(testFile, globals, [], doTypecheck=doTypecheck, extraDirs=extraDirs)
    except:
        handleCurrentException()
    return libDefs.dict['printTestResults']('Tutor:  ')

# globals already contain libDefs
def performChecks(check, testFile, globals, libDefs, doTypecheck=True, extraDirs=None, loadingFailed=False):
    prefix = ''
    if check and testFile:
        prefix = 'Student: '
    testResultsStudent = libDefs.printTestResults(prefix, loadingFailed)
    if check:
        testResultsInstr = {'total': 0, 'failing': 0}
        if testFile:
            testResultsInstr = runTestsInFile(testFile, globals, libDefs, doTypecheck=doTypecheck,
                                              extraDirs=extraDirs)
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

_tbPattern = re.compile(r'(\s*File\s+")([^"]+)(".*)')
def _rewriteFilenameInTracebackLine(s: str) -> str:
    # Match the pattern: File "filename", line number, in function
    match = re.match(_tbPattern, s)
    if match:
        prefix = match.group(1)
        filename = match.group(2)
        suffix = match.group(3)
        canonicalized = paths.canonicalizePath(filename)
        return prefix + canonicalized + suffix
    else:
        return s

def _rewriteFilenameInTraceback(s: str) -> str:
    lines = s.split('\n')
    result = []
    for l in lines:
        result.append(_rewriteFilenameInTracebackLine(l))
    return '\n'.join(result)

def handleCurrentException(exit=True, removeFirstTb=False, file=sys.stderr):
    (etype, val, tb) = sys.exc_info()
    if isinstance(val, SystemExit):
        die(val.code)
    isWyppError = isinstance(val, errors.WyppError)
    if isWyppError:
        extra = val.extraFrames
    else:
        extra = []
    frameList = (stacktrace.tbToFrameList(tb) if tb is not None else [])
    if frameList and removeFirstTb:
        frameList = frameList[1:]
    isBug = not isWyppError and not isinstance(val, SyntaxError) and \
        len(frameList) > 0 and stacktrace.isWyppFrame(frameList[-1])
    stackSummary = stacktrace.limitTraceback(frameList, extra, not isBug and not DEBUG)
    header = False
    for x in stackSummary.format():
        if not header:
            file.write('Traceback (most recent call last):\n')
            header = True
        file.write(_rewriteFilenameInTraceback(x))
    if isWyppError:
        s = str(val)
        if s and s[0] != '\n':
            file.write('\n')
        file.write(s)
        file.write('\n')
    else:
        for x in traceback.format_exception_only(etype, val):
            file.write(x)
    if isBug:
        file.write(f'BUG: the error above is most likely a bug in WYPP!')
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

# We cannot import typeguard at the top of the file because we might have to install it first.
def importTypeguard():
    global typeguard
    try:
        import typeguard  # type: ignore
    except ModuleNotFoundError as e:
        printStderr(f"Module typeguard not found, sys.path={sys.path}: {e}")
        die(1)

DEBUG = False

def main(globals, args, restArgs):
    # assumes that runner.main has been run

    if args.lang:
        if args.lang in i18n.allLanguages:
            i18n.setLang(args.lang)
        else:
            printStderr(f'Unsupported language {args.lang}. Supported: ' + ', '.join(i18n.allLanguages))
            sys.exit(1)

    importTypeguard()

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
    if not args.checkRunnable and (not args.quiet or args.verbose):
        printWelcomeString(fileToRun, version, doTypecheck=args.checkTypes)

    libDefs = prepareLib(onlyCheckRunnable=args.checkRunnable, enableTypeChecking=args.checkTypes)


    with paths.projectDir(os.path.abspath(os.getcwd())):
        globals['__name__'] = '__wypp__'
        sys.modules['__wypp__'] = sys.modules['__main__']
        loadingFailed = False
        try:
            verbose(f'running code in {fileToRun}')
            globals['__file__'] = fileToRun
            runStudentCode(fileToRun, globals, args.checkRunnable, restArgs,
                        doTypecheck=args.checkTypes, extraDirs=args.extraDirs)
        except Exception as e:
            verbose(f'Error while running code in {fileToRun}: {e}')
            handleCurrentException(exit=not isInteractive)
            loadingFailed = True

        performChecks(args.check, args.testFile, globals, libDefs, doTypecheck=args.checkTypes,
                    extraDirs=args.extraDirs, loadingFailed=loadingFailed)

    if isInteractive:
        enterInteractive(globals)
        if loadingFailed:
            print('NOTE: running the code failed, some definitions might not be available!')
            print()
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
    pass

    # FIXME
    # def showtraceback(self) -> None:
    #     handleCurrentException(exit=False, removeFirstTb=True, file=sys.stdout)

    # def runsource(self, source, filename="<input>", symbol="single"):
    #     try:
    #         code = self.compile(source, filename, symbol)
    #     except (OverflowError, SyntaxError, ValueError):
    #         self.showsyntaxerror(filename)
    #         return False
    #     if code is None:
    #         return True
    #     try:
    #         import ast
    #         tree = compile("\n".join(self.buffer), filename, symbol, flags=ast.PyCF_ONLY_AST, dont_inherit=True, optimize=-1)
    #         untypy.transform_tree(tree, filename)
    #         code = compile(tree, filename, symbol)
    #     except Exception as e:
    #         if hasattr(e, 'text') and e.text == "":
    #             pass
    #         else:
    #             traceback.print_tb(e.__traceback__)
    #     self.runcode(code)
    #     return False

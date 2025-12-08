import sys
import os
import importlib
import runpy
from dataclasses import dataclass

# local imports
from constants import *
import stacktrace
import instrument
from myLogging import *
from exceptionHandler import handleCurrentException
import utils

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


@dataclass
class RunSetup:
    def __init__(self, pathDir: str, args: list[str]):
        self.pathDir = os.path.abspath(pathDir)
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

def prepareLib(onlyCheckRunnable, enableTypeChecking):
    libDefs = None
    mod = 'wypp'
    verbose('Attempting to import ' + mod)
    wypp = importlib.import_module(mod)
    libDefs = Lib(wypp, True)
    verbose(f'Successfully imported module {mod} from file {wypp.__file__}')
    libDefs.initModule(enableChecks=not onlyCheckRunnable,
                       enableTypeChecking=enableTypeChecking,
                       quiet=onlyCheckRunnable)
    return libDefs

def debugModule(name):
    if name in sys.modules:
        m = sys.modules["copy"]
        print(f"Module {name} already loaded from:", getattr(m, "__file__", None))
    print("CWD:", os.getcwd())
    print("sys.path[0]:", sys.path[0])
    print("First few sys.path entries:")
    for p in sys.path[:5]:
        print("  ", p)

    spec = importlib.util.find_spec(name)
    print("Resolved spec:", spec)
    if spec:
        print("Origin:", spec.origin)
        print("Loader:", type(spec.loader).__name__)

def runCode(fileToRun, globals, doTypecheck=True, extraDirs=None) -> dict:
    if not extraDirs:
        extraDirs = []
    modName = os.path.basename(os.path.splitext(fileToRun)[0])
    with instrument.setupFinder(os.path.dirname(fileToRun), modName, extraDirs, doTypecheck):
        sys.dont_write_bytecode = True
        if DEBUG:
            debugModule(modName)
        res = runpy.run_module(modName, init_globals=globals, run_name='__wypp__', alter_sys=False)
        return res

def runStudentCode(fileToRun, globals, onlyCheckRunnable, doTypecheck=True, extraDirs=None) -> dict:
    doRun = lambda: runCode(fileToRun, globals, doTypecheck=doTypecheck, extraDirs=extraDirs)
    if onlyCheckRunnable:
        try:
            doRun()
        except:
            printStderr('Loading file %s crashed' % fileToRun)
            handleCurrentException()
        else:
            utils.die(0)
    return doRun()

# globals already contain libDefs
def runTestsInFile(testFile, globals, libDefs, doTypecheck=True, extraDirs=[]):
    printStderr()
    printStderr(f"Running tutor's tests in {testFile}")
    libDefs.resetTestCount()
    try:
        runCode(testFile, globals, doTypecheck=doTypecheck, extraDirs=extraDirs)
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
        utils.die(0 if failingSum < 1 else 1)

import sys
import constants
sys.path.insert(0, constants.CODE_DIR)

import sys
import os

# local imports
from constants import *
import i18n
import paths
from myLogging import *
import version as versionMod
import interactive
import runCode
import exceptionHandler
import cmdlineArgs

requiredVersion = (3, 12, 0)
def pythonVersionOk(v):
    (reqMajor, reqMinor, reqMicro) = requiredVersion
    if v.major < reqMajor or v.minor < reqMinor:
        return False
    if v.major == reqMajor and v.minor == reqMinor and v.micro < reqMicro:
        return False
    else:
        return True

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

def main(globals, argList=None):
    v = sys.version_info
    if not pythonVersionOk(v):
        vStr = sys.version.split()[0]
        reqVStr = '.'.join([str(x) for x in requiredVersion])
        print(f"""
Python in version {reqVStr} or newer is required. You are still using version {vStr}, please upgrade!
""")
        sys.exit(1)

    (args, restArgs) = cmdlineArgs.parseCmdlineArgs(argList)
    if args.verbose:
        enableVerbose()
    if args.debug:
        enableDebug()

    verbose(f'VERBOSE={args.verbose}, DEBUG={args.debug}')

    if args.lang:
        if args.lang in i18n.allLanguages:
            i18n.setLang(args.lang)
        else:
            printStderr(f'Unsupported language {args.lang}. Supported: ' + ', '.join(i18n.allLanguages))
            sys.exit(1)

    fileToRun: str = args.file
    if args.changeDir:
        os.chdir(os.path.dirname(fileToRun))
        fileToRun = os.path.basename(fileToRun)

    isInteractive = args.interactive
    version = versionMod.readVersion()
    if isInteractive:
        interactive.prepareInteractive(reset=not args.noClear)

    if fileToRun is None:
        return

    if not args.checkRunnable and (not args.quiet or args.verbose):
        printWelcomeString(fileToRun, version, doTypecheck=args.checkTypes)

    libDefs = runCode.prepareLib(onlyCheckRunnable=args.checkRunnable, enableTypeChecking=args.checkTypes)

    with (runCode.RunSetup(os.path.dirname(fileToRun), [fileToRun] + restArgs),
          paths.projectDir(os.path.abspath(os.getcwd()))):
        globals['__name__'] = '__wypp__'
        sys.modules['__wypp__'] = sys.modules['__main__']
        loadingFailed = False
        try:
            verbose(f'running code in {fileToRun}')
            globals['__file__'] = fileToRun
            globals = runCode.runStudentCode(fileToRun, globals, args.checkRunnable,
                                             doTypecheck=args.checkTypes, extraDirs=args.extraDirs)
        except Exception as e:
            verbose(f'Error while running code in {fileToRun}: {e}')
            exceptionHandler.handleCurrentException(exit=not isInteractive)
            loadingFailed = True

        runCode.performChecks(args.check, args.testFile, globals, libDefs, doTypecheck=args.checkTypes,
                              extraDirs=args.extraDirs, loadingFailed=loadingFailed)

        if isInteractive:
            interactive.enterInteractive(globals, args.checkTypes, loadingFailed)



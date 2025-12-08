import sys
import constants
sys.path.insert(0, constants.CODE_DIR)

import sys
import os

requiredVersion = (3, 12, 0)
def pythonVersionOk(v):
    (reqMajor, reqMinor, reqMicro) = requiredVersion
    if v.major < reqMajor or v.minor < reqMinor:
        return False
    if v.major == reqMajor and v.minor == reqMinor and v.micro < reqMicro:
        return False
    else:
        return True

if not pythonVersionOk(sys.version_info):
    vStr = sys.version.split()[0]
    reqVStr = '.'.join([str(x) for x in requiredVersion])
    print(f"""
Python in version {reqVStr} or newer is required. You are still using version {vStr}, please upgrade!
""")
    sys.exit(1)

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
import ansi

def printWelcomeString(file, version, doTypecheck):
    cwd = os.getcwd() + "/"
    if file.startswith(cwd):
        file = file[len(cwd):]
    versionStr = '' if not version else 'Version %s, ' % version
    pythonVersion = sys.version.split()[0]
    tycheck = ''
    if not doTypecheck:
        tycheck = ', no typechecking'
    msg = i18n.tr('=== WELCOME to ') + '"Write Your Python Program" ' + \
          '(%sPython %s, %s%s) ===' % (versionStr, pythonVersion, file, tycheck)
    fullMsg = (10 * '\n') + ansi.green(msg) + '\n'
    printStderr(fullMsg)

def main(globals, argList=None):
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
    if not os.path.exists(fileToRun):
        printStderr(f'File {fileToRun} does not exist')
        sys.exit(1)
    if args.changeDir:
        d = os.path.dirname(fileToRun)
        os.chdir(d)
        fileToRun = os.path.basename(fileToRun)
        debug(f'Changed directory to {d}, fileToRun={fileToRun}')

    isInteractive = args.interactive
    version = versionMod.readVersion()

    if fileToRun is None:
        return

    if not args.checkRunnable and (not args.quiet or args.verbose):
        printWelcomeString(fileToRun, version, doTypecheck=args.checkTypes)

    libDefs = runCode.prepareLib(onlyCheckRunnable=args.checkRunnable, enableTypeChecking=args.checkTypes)

    runDir = os.path.dirname(fileToRun)
    with (runCode.RunSetup(runDir, [fileToRun] + restArgs),
          paths.projectDir(os.path.abspath(os.getcwd()))):
        globals['__name__'] = '__wypp__'
        sys.modules['__wypp__'] = sys.modules['__main__']
        loadingFailed = False
        try:
            verbose(f'running code in {fileToRun}')
            debug(f'sys.path: {sys.path}')
            globals['__file__'] = fileToRun
            globals = runCode.runStudentCode(fileToRun, globals, args.checkRunnable,
                                             doTypecheck=args.checkTypes, extraDirs=args.extraDirs)
        except Exception as e:
            verbose(f'Error while running code in {fileToRun}')
            exceptionHandler.handleCurrentException(exit=not isInteractive)
            loadingFailed = True

        runCode.performChecks(args.check, args.testFile, globals, libDefs, doTypecheck=args.checkTypes,
                              extraDirs=args.extraDirs, loadingFailed=loadingFailed)

        if args.repls:
            import replTester
            replTester.testRepls(args.repls, globals)

        if isInteractive:
            interactive.enterInteractive(globals, args.checkTypes, loadingFailed)



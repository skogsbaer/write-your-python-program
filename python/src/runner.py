# Step 1 of the runner. Only installes typeguard and then passes control to runner2. The purpose
# of splitting the runner in two modules is to allow step2 to import typeguard.

import sys
import argparse
import os
from pathlib import Path
import shutil
import site

from myLogging import *
from runnerCommon import *

FILES_TO_INSTALL = ['writeYourProgram.py', 'drawingLib.py', '__init__.py']
TYPEGUARD_DIR = os.path.join(LIB_DIR, "..", "deps", "typeguard")
TYPEGUARD_MODULE_NAME = 'typeguard'
SITELIB_DIR = os.path.join(LIB_DIR, "..", "site-lib")

__wypp_runYourProgram = 1

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
    parser.add_argument('--debug', dest='debug', action='store_const',
                        const=True, default=False,
                        help='Enable debugging')
    parser.add_argument('--quiet', dest='quiet', action='store_const',
                        const=True, default=False, help='Be extra quiet')
    parser.add_argument('--lang', dest='lang',
                        type=str, help='Display error messages in this language (either en or de).')
    parser.add_argument('--no-clear', dest='noClear', action='store_const',
                        const=True, default=False, help='Do not clear the terminal')
    parser.add_argument('--test-file', dest='testFile',
                        type=str, help='Run additional tests contained in this file.')
    parser.add_argument('--extra-dir', dest='extraDirs', action='append', type=str,
                        help='Also typechecks files contained in the given directory.\n' \
                            'By default, only files in the same directory as the main file are\n' \
                            'checked.')
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

requiredVersion = (3, 12, 0)
def versionOk(v):
    (reqMajor, reqMinor, reqMicro) = requiredVersion
    if v.major < reqMajor or v.minor < reqMinor:
        return False
    if v.major == reqMajor and v.minor == reqMinor and v.micro < reqMicro:
        return False
    else:
        return True

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
        allEq2 = installFromDir(TYPEGUARD_DIR, targetDir, TYPEGUARD_MODULE_NAME)
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

def main(globals, argList=None):
    v = sys.version_info
    if not versionOk(v):
        vStr = sys.version.split()[0]
        reqVStr = '.'.join([str(x) for x in requiredVersion])
        print(f"""
Python in version {reqVStr} or newer is required. You are still using version {vStr}, please upgrade!
""")
        sys.exit(1)

    (args, restArgs) = parseCmdlineArgs(argList)
    if args.verbose:
        enableVerbose()
    if args.debug:
        enableDebug()

    verbose(f'VERBOSE={args.verbose}, DEBUG={args.debug}')

    installLib(args.installMode)
    if args.installMode == InstallMode.dontInstall:
        if SITELIB_DIR not in sys.path:
            sys.path.insert(0, SITELIB_DIR)
    else:
        if site.USER_SITE not in sys.path:
            if not site.ENABLE_USER_SITE or site.USER_SITE is None:
                printStderr(f"User site-packages disabled ({site.USER_SITE}. This might cause problems importing wypp or typeguard.")
            else:
                verbose(f"Adding user site-package directory {site.USER_SITE} to sys.path")
                sys.path.append(site.USER_SITE)
    import runner2
    runner2.main(globals, args, restArgs)

import argparse
import sys
import utils
from myLogging import *

def parseCmdlineArgs(argList):
    parser = argparse.ArgumentParser(description='Run Your Program!',
                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--check-runnable', dest='checkRunnable', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if loading the file raises errors')
    parser.add_argument('--check', dest='check', action='store_const',
                        const=True, default=False,
                        help='Abort with exit code 1 if there are test errors.')
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
    parser.add_argument('--repl', action='extend', type=str, nargs='+', default=[], dest='repls',
                        help='Run repl tests in the file given')
    parser.add_argument('file', metavar='FILE',
                        help='The file to run', nargs='?')
    if argList is None:
        argList = sys.argv[1:]
    try:
        args, restArgs = parser.parse_known_args(argList)
    except SystemExit as ex:
        utils.die(ex.code)
    if args.file and not args.file.endswith('.py'):
        printStderr(f'ERROR: file {args.file} is not a python file')
        utils.die()
    return (args, restArgs)

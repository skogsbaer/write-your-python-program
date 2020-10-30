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

parser = argparse.ArgumentParser(description='Run Your Program!')
parser.add_argument('file', metavar='FILE',
                    help='The file to run')
parser.add_argument('--check', dest='check', action='store_const',
                    const=True, default=False,
                    help='Abort with exit code 1 if there are test errors.')

try:
    args = parser.parse_args()
except SystemExit as ex:
    os._exit(ex.code)

fileToRun = args.file
isInteractive = sys.flags.interactive

if isInteractive:
    print('\n')

if not fileToRun.endswith('.py'):
    print("FEHLER: die angegebene Datei ist keine Python Datei.")
    os._exit(0)

if isInteractive:
    # clear the terminal, reset on Mac OSX and Linux. This prevents strange history bugs where
    # the command just entered is echoed again (2020-10-14).
    os.system('cls' if os.name == 'nt' else 'reset')

libDir = os.path.dirname(__file__)

version = None
try:
    with open(os.path.join(libDir, '..', '..', 'package.json')) as file:
        content = file.read()
        d = json.loads(content)
        version = d['version']
except:
    pass
libFile = os.path.join(libDir, 'writeYourProgram.py')
libDefs = runpy.run_path(libFile)
libDefs['_initModule'](fileToRun, version, pythonVersion)
userDefs = runpy.run_path(fileToRun, libDefs)
failing = libDefs['_finishModule']()

if args.check:
    os._exit(0 if failing < 1 else 1)

for k, v in userDefs.items():
    globals()[k] = v

if isInteractive:
    print()

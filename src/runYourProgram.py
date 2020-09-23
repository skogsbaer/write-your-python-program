import sys
import os
import os.path
import runpy
import argparse

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

libDir = os.path.dirname(__file__)
libFile = os.path.join(libDir, 'writeYourProgram.py')
libDefs = runpy.run_path(libFile)
libDefs['initModule'](fileToRun)
userDefs = runpy.run_path(fileToRun, libDefs)
failing = libDefs['finishModule']()

if args.check:
    os._exit(0 if failing < 1 else 1)

for k, v in userDefs.items():
    globals()[k] = v

if isInteractive:
    print("Beenden mit Ctrl-D oder exit()")

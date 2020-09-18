import sys
import os
import os.path
import runpy

args = sys.argv

if len(args) < 2:
    print("FEHLER: du must die auszuführende Datei angeben.")
    os._exit(1)
elif len(args) > 2:
    print("FEHLER: zu viele Argument, da darfst nur die auszuführende Datei angeben.")
    os._exit(1)

fileToRun = args[1]
if not fileToRun.endswith('.py'):
    print("FEHLER: die angegebene Datei ist keine Python Datei.")
    os._exit(0)

libDir = os.path.dirname(__file__)
libFile = os.path.join(libDir, 'writeYourProgram.py')
libDefs = runpy.run_path(libFile)
libDefs['initModule'](fileToRun)
_userDefs = runpy.run_path(fileToRun, libDefs)
libDefs['finishModule']()
print("Beenden mit Ctrl-D oder exit()")

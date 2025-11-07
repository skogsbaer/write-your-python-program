
import sys
import os
import code
from dataclasses import dataclass

# local imports
from constants import *
from myLogging import *
from exceptionHandler import handleCurrentException

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

class TypecheckedInteractiveConsole(code.InteractiveConsole):
    def showtraceback(self) -> None:
        handleCurrentException(exit=False, removeFirstTb=True, file=sys.stdout)

def enterInteractive(userDefs: dict, checkTypes: bool, loadingFailed: bool):
    for k, v in userDefs.items():
        globals()[k] = v
    print()
    if checkTypes:
        consoleClass = TypecheckedInteractiveConsole
    else:
        consoleClass = code.InteractiveConsole
    historyFile = getHistoryFilePath()
    try:
        import readline
    except:
        readline = None
    if readline:
        readline.parse_and_bind('tab: complete')
        if historyFile and os.path.exists(historyFile):
            readline.read_history_file(historyFile)
    try:
        consoleClass(locals=userDefs).interact(banner="", exitmsg='')
    finally:
        if readline and historyFile:
            readline.set_history_length(HISTORY_SIZE)
            readline.write_history_file(historyFile)

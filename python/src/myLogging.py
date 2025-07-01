import utils
import sys

VERBOSE = False # set via commandline
DEBUG = utils.getEnv("WYPP_DEBUG", bool, False)

def enableVerbose():
    global VERBOSE
    VERBOSE = True

def printStderr(s=''):
    sys.stderr.write(s + '\n')

def verbose(s):
    if VERBOSE or DEBUG:
        printStderr('[V] ' + str(s))

def debug(s):
    if DEBUG:
        printStderr('[D] ' + str(s))

import re
import sys
import os

RESET         = "\u001b[0;0m"
BOLD          = "\u001b[1m"
REVERSE       = "\u001b[2m"

BLACK         = "\u001b[0;30m"
BLUE          = "\u001b[0;34m"
GREEN         = "\u001b[0;32m"
CYAN          = "\u001b[0;36m"
RED           = "\u001b[0;31m"
PURPLE        = "\u001b[0;35m"
BROWN         = "\u001b[0;33m"
GRAY          = "\u001b[0;37m"
DARK_GRAY     = "\u001b[1;30m"
LIGHT_BLUE    = "\u001b[1;34m"
LIGHT_GREEN   = "\u001b[1;32m"
LIGHT_CYAN    = "\u001b[1;36m"
LIGHT_RED     = "\u001b[1;31m"
LIGHT_PURPLE  = "\u001b[1;35m"
YELLOW        = "\u001b[1;33m"
WHITE         = "\u001b[1;37m"

def useColors():
    if "NO_COLOR" in os.environ:
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True

def color(s, color):
    if useColors():
        return color + s + RESET
    else:
        return s

def green(s):
    return color(s, GREEN + BOLD)

def red(s):
    return color(s, RED + BOLD)

def blue(s):
    return color(s, BLUE + BOLD)

_ANSI_ESCAPE_RE = re.compile(r'\u001b\[[0-9;]*m')
def stripAnsi(s: str) -> str:
    return _ANSI_ESCAPE_RE.sub('', s)

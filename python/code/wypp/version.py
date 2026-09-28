import json
import os
from typing import Optional

from .constants import *
from .myLogging import *
from . import utils

# The root directory of the repository or the vscode extension
BASE_DIR = os.path.normpath(os.path.join(CODE_DIR, '..', '..'))

def readVersion(baseDir: str = BASE_DIR) -> Optional[str]:
    """
    Returns the version from package.json in baseDir, with suffix '-git' if
    baseDir is a git repository. Returns None if the version cannot be determined.
    """
    try:
        content = utils.readFile(os.path.join(baseDir, 'package.json'))
        version = json.loads(content)['version']
    except Exception as e:
        verbose(f'Could not read version from package.json in {baseDir}: {e}')
        return None
    if os.path.exists(os.path.join(baseDir, '.git')):
        version = f'{version}-git'
    return version

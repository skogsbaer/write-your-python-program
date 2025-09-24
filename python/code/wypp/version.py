import os
import json
import subprocess
from dataclasses import dataclass

# local imports
from constants import *
from myLogging import *
import utils

def readGitVersion():
    thisDir = os.path.basename(SOURCE_DIR)
    baseDir = os.path.join(SOURCE_DIR, '..', '..')
    if thisDir == 'src' and os.path.isdir(os.path.join(baseDir, '.git')):
        try:
            h = subprocess.check_output(['git', '-C', baseDir, 'rev-parse', '--short', 'HEAD'],
                encoding='UTF-8').strip()
            changes = subprocess.check_output(
                    ['git', '-C', baseDir, 'status', '--porcelain', '--untracked-files=no'],
                    encoding='UTF-8').strip()
            if changes:
                return f'git-{h}-dirty'
            else:
                return f'git-{h}'
        except subprocess.CalledProcessError:
            return 'git-?'
    else:
        return None

def readVersion():
    version = readGitVersion()
    if version is not None:
        return version
    try:
        content = utils.readFile(os.path.join(SOURCE_DIR, '..', '..', 'package.json'))
        d = json.loads(content)
        version = d['version']
    except:
        pass
    return version

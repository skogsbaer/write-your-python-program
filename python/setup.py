#!/usr/bin/env python

from distutils.core import setup
import setuptools
import os
import json

TOP_DIR = os.path.join(os.path.dirname(__file__), '..')
VERSION_FILE = 'VERSION'

def writeVersionFile():
    pkgJson = os.path.join(TOP_DIR, 'package.json')
    if os.path.isfile(pkgJson):
        content = open(pkgJson).read()
        d = json.loads(content)
        version = d['version']
        open(VERSION_FILE, 'w').write(version)

writeVersionFile()

def readVersion():
    return open(VERSION_FILE).read().strip()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name='wypp',
      version=readVersion(),
      description='A user-friendly python programming environment for beginners',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Stefan Wehr',
      author_email='stefan.wehr@hs-offenburg.de',
      url='https://github.com/skogsbaer/write-your-python-program',
      package_dir={'wypp': 'src', 'untypy': 'deps/untypy/untypy'},
      packages=['wypp'] + setuptools.find_packages("deps/untypy", exclude=['test', 'test.*']),
      python_requires='>=3.9',
      scripts=['wypp']
      )

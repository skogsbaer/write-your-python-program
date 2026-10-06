import json
import os
import tempfile
import unittest
import wypp.version as version

# package.json lives in the root directory of the repository
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')

def writePackageJson(d: str, v: str):
    with open(os.path.join(d, 'package.json'), 'w', encoding='utf-8') as f:
        json.dump({'name': 'write-your-python-program', 'version': v}, f)

class TestVersion(unittest.TestCase):

    def test_readVersionFromRepo(self):
        with open(os.path.join(BASE_DIR, 'package.json'), encoding='utf-8') as f:
            expected = json.load(f)['version']
        if os.path.exists(os.path.join(BASE_DIR, '.git')):
            expected = expected + '-git'
        self.assertEqual(version.readVersion(), expected)

    def test_readVersionWithoutGit(self):
        with tempfile.TemporaryDirectory() as d:
            writePackageJson(d, '1.2.3')
            self.assertEqual(version.readVersion(d), '1.2.3')

    def test_readVersionWithGit(self):
        with tempfile.TemporaryDirectory() as d:
            writePackageJson(d, '1.2.3')
            os.mkdir(os.path.join(d, '.git'))
            self.assertEqual(version.readVersion(d), '1.2.3-git')

    def test_readVersionWithoutPackageJson(self):
        with tempfile.TemporaryDirectory() as d:
            os.mkdir(os.path.join(d, '.git'))
            self.assertIsNone(version.readVersion(d))

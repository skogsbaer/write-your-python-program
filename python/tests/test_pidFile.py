import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import pidFile

class TestPidFile(unittest.TestCase):

    def setUp(self):
        self.tmpDir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpDir.name, 'wypp.pid')
        # writePidFile registers removePidFile with atexit; don't do this in the test process
        patcher = mock.patch('pidFile.atexit.register')
        self.atexitRegister = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        pidFile.removePidFile()
        self.tmpDir.cleanup()

    def readPidFile(self):
        with open(self.path, encoding='utf-8') as f:
            return json.load(f)

    def test_writeWritesPidAndPgid(self):
        pidFile.writePidFile(self.path)
        expectedPgid = os.getpgid(0) if hasattr(os, 'getpgid') else None
        self.assertEqual(self.readPidFile(), {'pid': os.getpid(), 'pgid': expectedPgid})

    def test_fileStaysOpenAfterWrite(self):
        pidFile.writePidFile(self.path)
        self.assertIsNotNone(pidFile._openPidFile)
        self.assertFalse(pidFile._openPidFile.closed)

    def test_writeRegistersRemoveWithAtexit(self):
        pidFile.writePidFile(self.path)
        self.atexitRegister.assert_called_once_with(pidFile.removePidFile)

    def test_writeTwiceRaises(self):
        pidFile.writePidFile(self.path)
        with self.assertRaises(Exception):
            pidFile.writePidFile(os.path.join(self.tmpDir.name, 'other.pid'))

    def test_removeClosesAndDeletes(self):
        pidFile.writePidFile(self.path)
        f = pidFile._openPidFile
        pidFile.removePidFile()
        self.assertTrue(f.closed)
        self.assertFalse(os.path.exists(self.path))
        self.assertIsNone(pidFile._openPidFile)

    def test_writeAgainAfterRemove(self):
        pidFile.writePidFile(self.path)
        pidFile.removePidFile()
        pidFile.writePidFile(self.path)
        self.assertEqual(self.readPidFile()['pid'], os.getpid())

    def test_removeWithoutWriteIsNoop(self):
        pidFile.removePidFile()
        self.assertIsNone(pidFile._openPidFile)

    def test_removeTwiceIsHarmless(self):
        pidFile.writePidFile(self.path)
        pidFile.removePidFile()
        pidFile.removePidFile()
        self.assertFalse(os.path.exists(self.path))

    def test_removeAfterFileDeletedByOthers(self):
        # e.g. the extension deleted a PID file it considered stale (possible on Unix)
        pidFile.writePidFile(self.path)
        f = pidFile._openPidFile
        os.remove(self.path)
        pidFile.removePidFile()
        self.assertTrue(f.closed)
        self.assertIsNone(pidFile._openPidFile)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows only')
    def test_openFileCannotBeDeletedOnWindows(self):
        # The extension relies on this to detect that the program is still running.
        pidFile.writePidFile(self.path)
        with self.assertRaises(PermissionError):
            os.remove(self.path)
        pidFile.removePidFile()
        self.assertFalse(os.path.exists(self.path))

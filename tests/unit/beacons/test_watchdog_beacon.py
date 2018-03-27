# coding: utf-8

# Python libs
from __future__ import absolute_import
import os
import shutil
import tempfile
import time

# Salt libs
import salt.utils.files
from salt.beacons import watchdog

# Salt testing libs
from tests.support.unit import skipIf, TestCase
from tests.support.mixins import LoaderModuleMockMixin


@skipIf(not watchdog.HAS_WATCHDOG, 'watchdog is not available')
class IWatchdogBeaconTestCase(TestCase, LoaderModuleMockMixin):
    '''
    Test case for salt.beacons.watchdog
    '''

    def setup_loader_modules(self):
        return {watchdog: {}}

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_config(self):
        config = [{}]
        ret = watchdog.beacon(config)
        self.assertEqual(ret, [])

    def test_file_create(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['create']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        ret = watchdog.beacon(config)
        self.assertEqual(ret, [])

        with salt.utils.files.fopen(path, 'w') as f:
            pass

        time.sleep(1)  # oups

        ret = watchdog.beacon(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'created')


    def test_file_modified(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['modify']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        ret = watchdog.beacon(config)
        self.assertEqual(ret, [])

        with salt.utils.files.fopen(path, 'w') as f:
            f.write('some content')

        time.sleep(1)  # oups

        ret = watchdog.beacon(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'modified')

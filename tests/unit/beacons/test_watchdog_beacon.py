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


def check_events(config):
    total_delay = 1
    delay_per_loop = 20e-3

    for _ in range(int(total_delay / delay_per_loop)):
        events = watchdog.beacon(config)

        if events:
            return events

        time.sleep(delay_per_loop)

    return []


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

        self.assertEqual(watchdog.beacon(config), [])

        with salt.utils.files.fopen(path, 'w') as f:
            pass

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'created')


    def test_file_modified(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['modify']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        self.assertEqual(watchdog.beacon(config), [])

        with salt.utils.files.fopen(path, 'w') as f:
            f.write('some content')

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'modified')

    def test_file_deleted(self):
        path = os.path.join(self.tmpdir, 'tmpfile')
        with salt.utils.files.fopen(path, 'w'):
            pass

        config = [{'files': {path: {'mask': ['delete']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        self.assertEqual(watchdog.beacon(config), [])

        os.remove(path)

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'deleted')

    def test_file_moved(self):
        path = os.path.join(self.tmpdir, 'tmpfile')
        with salt.utils.files.fopen(path, 'w'):
            pass

        config = [{'files': {path: {'mask': ['move']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        self.assertEqual(watchdog.beacon(config), [])

        os.rename(path, path + '_moved')

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'moved')

    def DISABLED_test_file_create_in_directory(self):
        config = [{'files': {self.tmpdir: {'mask': ['create', 'modify']}}}]
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

        self.assertEqual(watchdog.beacon(config), [])

        path = os.path.join(self.tmpdir, 'tmpfile')
        with salt.utils.files.fopen(path, 'w') as f:
            pass

        ret = check_events(config)
        self.assertEqual(len(ret), 2)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'created')
        self.assertEqual(ret[1]['path'], self.tmpdir)
        self.assertEqual(ret[1]['change'], 'modified')

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


def create(path, content=None):
    with salt.utils.files.fopen(path, 'w') as f:
        if content:
            f.write(content)


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
        watchdog.close({})
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def assertValid(self, config):
        ret = watchdog.validate(config)
        self.assertEqual(ret, (True, 'Valid beacon configuration'))

    def test_empty_config(self):
        config = [{}]
        ret = watchdog.beacon(config)
        self.assertEqual(ret, [])

    def test_file_create(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['create']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        create(path)

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'created')

    def test_file_modified(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['modify']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        create(path, 'some content')

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'modified')

    def test_file_no_modified_on_deletion(self):
        path = os.path.join(self.tmpdir, 'tmpfile')

        config = [{'files': {path: {'mask': ['modify']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        create(path)
        self.assertEqual(watchdog.beacon(config), [])

        os.remove(path)

        ret = check_events(config)
        self.assertEqual(watchdog.beacon(config), [])

    def test_file_deleted(self):
        path = os.path.join(self.tmpdir, 'tmpfile')
        create(path)

        config = [{'files': {path: {'mask': ['delete']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        os.remove(path)

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'deleted')

    def test_file_moved(self):
        path = os.path.join(self.tmpdir, 'tmpfile')
        create(path)

        config = [{'files': {path: {'mask': ['move']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        os.rename(path, path + '_moved')

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'moved')

    def test_only_monitors_interesting_files(self):
        file1 = os.path.join(self.tmpdir, 'file1')
        file2 = os.path.join(self.tmpdir, 'file2')

        config = [{'files': {file1: {'mask': ['create']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        create(file1)
        create(file2)

        ret = check_events(config)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]['path'], file1)
        self.assertEqual(ret[0]['change'], 'created')

    def test_file_create_in_directory(self):
        config = [{'files': {self.tmpdir: {'mask': ['create', 'modify']}}}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        path = os.path.join(self.tmpdir, 'tmpfile')
        create(path)

        ret = check_events(config)
        self.assertEqual(len(ret), 2)
        self.assertEqual(ret[0]['path'], path)
        self.assertEqual(ret[0]['change'], 'created')
        self.assertEqual(ret[1]['path'], self.tmpdir)
        self.assertEqual(ret[1]['change'], 'modified')

    def test_config_uses_default_mask(self):
        path = os.path.join(self.tmpdir, 'tmpfile')
        moved = path + '_moved'

        config = [{'files': {
            path: {},
            moved: {},
        }}]
        self.assertValid(config)
        self.assertEqual(watchdog.beacon(config), [])

        create(path)
        create(path, 'modified content')
        os.rename(path, moved)
        os.remove(moved)

        ret = check_events(config)
        self.assertEqual(len(ret), 4)

    def DISABLED_test_directory_is_moved_created_etc(self):
        pass

    def DISABLED_test_a_file_moved_outside_watched_space_is_reported_as_deleted(self):
        pass

    def DISABLED_test_mask_is_recursive(self):
        pass

    # and all the other tests for recursive behavior ...

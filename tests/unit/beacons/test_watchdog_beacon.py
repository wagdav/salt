# coding: utf-8

# Python libs
from __future__ import absolute_import
import os
import shutil
import tempfile

# Salt libs
import salt.utils.files
from salt.beacons import watchdog

# Salt testing libs
from tests.support.unit import skipIf, TestCase
from tests.support.mixins import LoaderModuleMockMixin
# Third-party libs

import logging
log = logging.getLogger(__name__)


@skipIf(not watchdog.HAS_WATCHDOG, 'watchdog is not available')
class INotifyBeaconTestCase(TestCase, LoaderModuleMockMixin):
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

# -*- coding: utf-8 -*-
'''
watchdog beacon
'''
# Import Python libs
from __future__ import absolute_import
import collections
import fnmatch
import os
import re

# Import salt libs
import salt.ext.six

# Import third party libs
try:
    from watchdog.observers import Observer
    from watchdog.events import LoggingEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

__virtualname__ = 'watchdog'

import logging
log = logging.getLogger(__name__)

def __virtual__():
    if HAS_WATCHDOG:
        return __virtualname__
    return False


def _get_notifier(config):
    '''
    Check the context for the notifier and construct it if not present
    '''
   
    path = '/tmp/important_file'

    if 'watchdog.observer' not in __context__:
        __context__['watchdog.queue'] = collections.deque()
        event_handler = LoggingEventHandler()
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(path), recursive=True)
        observer.start()
        __context__['watchdog.observer'] = observer 
    return __context__['watchdog.observer']

def __validate__(config):
    '''
    Validate the beacon configuration
    '''
    return True, 'Valid beacon configuration'


def beacon(config):
    '''
    '''

    _get_notifier(config)
    return []


def close(config):
    ''' close '''

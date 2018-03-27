# -*- coding: utf-8 -*-
'''
watchdog beacon

Watch files and translate the changes into salt events

:depends:   - watchdog Python module >= 0.8.3

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
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

__virtualname__ = 'watchdog'

import logging
log = logging.getLogger(__name__)


class Handler(FileSystemEventHandler):
    def __init__(self, queue):
        super(FileSystemEventHandler, self).__init__()
        self.queue = queue

    def on_modified(self, event):
        log.debug("on_modified event received: %s", event)
        self.queue.append(event)


def __virtual__():
    if HAS_WATCHDOG:
        return __virtualname__
    return False


def _get_notifier(config):
    '''
    Check the context for the notifier and construct it if not present
    '''

    path = '/tmp/mydir/important_file'

    if 'watchdog.observer' not in __context__:
        __context__['watchdog.queue'] = collections.deque()
        event_handler = Handler(__context__['watchdog.queue'])
        observer = Observer()
        for path in config.get('files', {}):
            observer.schedule(event_handler, os.path.dirname(path), recursive=True)

        observer.start()
        __context__['watchdog.observer'] = observer
    return __context__['watchdog.observer']


def __validate__(config):
    '''
    Validate the beacon configuration
    '''
    return True, 'Valid beacon configuration'


def to_salt_event(event):
    return {
        'tag': 'watchdog',
        'src_path': event.src_path,
        'type': event.event_type,
    }


def beacon(config):
    '''
    '''
    _config = {}
    map(_config.update, config)

    _get_notifier(_config)

    queue = __context__['watchdog.queue']
    log.debug("The queue contains: %s", queue)

    ret = []
    while len(queue):
        log.debug("will send %s", queue[0])
        ret.append(to_salt_event(queue.popleft()))

    return ret


def close(config):
    if 'watchdog.observer' in __context__:
        __context__['watchdog.observer'].stop()
        del __context__['watchdog.observer']

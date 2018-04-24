# -*- coding: utf-8 -*-
'''
watchdog beacon

Watch files and translate the changes into salt events

:depends:   - watchdog Python module >= 0.8.3

'''
# Import Python libs
from __future__ import absolute_import
import collections
import os

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

DEFAULT_MASK = [
    'create',
    'delete',
    'modify',
    'move',
]


class Handler(FileSystemEventHandler):
    def __init__(self, config, queue):
        super(FileSystemEventHandler, self).__init__()
        self.config = config
        self.queue = queue

    def on_created(self, event):
        self._append_if_mask(event, 'create')

    def on_modified(self, event):
        self._append_if_mask(event, 'modify')

    def on_deleted(self, event):
        self._append_if_mask(event, 'delete')

    def on_moved(self, event):
        self._append_if_mask(event, 'move')

    def _append_if_mask(self, event, mask):
        logging.debug(event)

        self._append_path_if_mask(event, event.src_path, mask)

        if not event.is_directory:
            parent_dir = os.path.dirname(event.src_path)
            self._append_path_if_mask(event, parent_dir, mask)

    def _append_path_if_mask(self, event, path, mask):
        if path in self.config.get('files', {}):
            if mask in self.config['files'][path].get('mask', DEFAULT_MASK):
                self.queue.append(event)


def __virtual__():
    if HAS_WATCHDOG:
        return __virtualname__
    return False


def _get_notifier(config):
    '''
    Check the context for the notifier and construct it if not present
    '''

    if 'watchdog.observer' not in __context__:
        __context__['watchdog.queue'] = collections.deque()
        event_handler = Handler(config, __context__['watchdog.queue'])
        observer = Observer()
        for path in config.get('files', {}):
            if os.path.isdir(path):
                observer.schedule(event_handler, path)
            else:
                observer.schedule(event_handler, os.path.dirname(path))

        observer.start()
        __context__['watchdog.observer'] = observer
    return __context__['watchdog.observer']


def validate(config):
    '''
    Validate the beacon configuration
    '''
    return True, 'Valid beacon configuration'


def to_salt_event(event):
    return {
        'tag': 'watchdog',
        'path': event.src_path,
        'change': event.event_type,
    }


def beacon(config):
    '''
    Watch the configured files

    Example Config

    .. code-block:: yaml

        beacons:
          watchdog:
            - files:
                /path/to/file/or/dir:
                  mask:
                    - create
                    - modify
                    - delete
                    - move

    The mask list can contain the following events (the default mask is create,
    delete, and modify):
    * create            - File or directory is created in watched directory
    * modify            - File modified
    * delete            - File or directory is deleted from watched directory
    * moved             - File or directory is moved or renamed
    '''

    _config = {}
    list(map(_config.update, config))

    _get_notifier(_config)

    queue = __context__['watchdog.queue']

    ret = []
    while len(queue):
        ret.append(to_salt_event(queue.popleft()))

    return ret


def close(config):
    if 'watchdog.observer' in __context__:
        __context__['watchdog.observer'].stop()
        del __context__['watchdog.observer']

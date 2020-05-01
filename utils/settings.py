""" Module to handle loading and writing the default NMSDK settings file. """

# stdlib imports
import json
import os.path as op
import os
from platform import system as os_name

# local imports
from .io import get_MBINCompiler_location  # noqa


_os_name = os_name()
if _os_name == 'Windows':
    SETTINGS_DIR = op.join(os.getenv('APPDATA'), 'NMSDK')
elif _os_name == 'Linux':
    SETTINGS_DIR = op.expanduser('~/NMSDK')
elif _os_name == 'Darwin':
    # UNTESTED!
    SETTINGS_DIR = op.join(op.expanduser('~'), 'Library', 'NMSDK')
else:
    raise ValueError('Current operating system is not supported sorry!')
SETTINGS_FNAME = 'settings.json'

DEFAULT_SETTINGS = {'export_directory': 'CUSTOMMODELS',
                    'group_name': '',
                    'MBINCompiler_location': get_MBINCompiler_location()}


def read_settings():
    """ Read the settings from the settings file. """
    if not op.exists(op.join(SETTINGS_DIR, SETTINGS_FNAME)):
        return DEFAULT_SETTINGS
    with open(op.join(SETTINGS_DIR, SETTINGS_FNAME), 'r') as f:
        data = json.load(f)
        # Update the settings with any default settings
        for key, value in DEFAULT_SETTINGS.items():
            if key not in data:
                data[key] = value
        return data


def write_settings(settings):
    """ Write the settings provided to the settings file. """
    if not op.exists(SETTINGS_DIR):
        os.mkdir(SETTINGS_DIR)
    with open(op.join(SETTINGS_DIR, SETTINGS_FNAME), 'w') as f:
        json.dump(settings, f)

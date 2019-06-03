""" Module to handle loading and writing the default NMSDK settings file. """

import json
import os.path as op
import os


SETTINGS_DIR = op.join(op.expanduser('APPDATA'), 'NMSDK')
SETTINGS_FNAME = 'settings.json'

DEFAULT_SETTINGS = {'export_directory': 'CUSTOMMODELS',
                    'group_name': ''}


def read_settings():
    """ Read the settings from the settings file. """
    if not op.exists(op.join(SETTINGS_DIR, SETTINGS_FNAME)):
        return DEFAULT_SETTINGS
    with open(op.join(SETTINGS_DIR, SETTINGS_FNAME), 'r') as f:
        return json.load(f)


def write_settings(settings):
    """ Write the settings provided to the settings file. """
    if not op.exists(SETTINGS_DIR):
        os.mkdir(SETTINGS_DIR)
    with open(op.join(SETTINGS_DIR, SETTINGS_FNAME), 'w') as f:
        json.dump(settings, f)

""" Module to handle loading and writing the default NMSDK settings file. """

import json
import os
import os.path as op
from platform import system as os_name

_os_name = os_name()
if _os_name == "Windows":
    SETTINGS_DIR = op.join(os.getenv("APPDATA", ""), "NMSDK")
elif _os_name == "Linux":
    SETTINGS_DIR = op.expanduser("~/NMSDK")
elif _os_name == "Darwin":
    # UNTESTED!
    SETTINGS_DIR = op.join(op.expanduser("~"), "Library", "NMSDK")
else:
    raise ValueError("I don't know what OS you're running, but it's supported sorry!")
SETTINGS_FNAME = "settings.json"

DEFAULT_SETTINGS = {
    "export_directory": "CUSTOMMODELS",
    "group_name": "",
}


def read_settings():
    """ Read the settings from the settings file. """
    if not op.exists(op.join(SETTINGS_DIR, SETTINGS_FNAME)):
        return DEFAULT_SETTINGS
    with open(op.join(SETTINGS_DIR, SETTINGS_FNAME), "r") as f:
        data = json.load(f)
        # Update the settings with any default settings
        for key, value in DEFAULT_SETTINGS.items():
            if key not in data:
                data[key] = value
        return data


def write_settings(settings) -> str:
    """ Write the settings provided to the settings file. """
    if not op.exists(SETTINGS_DIR):
        os.mkdir(SETTINGS_DIR)
    dest = op.join(SETTINGS_DIR, SETTINGS_FNAME)
    with open(dest, "w") as f:
        json.dump(settings, f)
    return dest

from pathlib import Path


def get_NMS_dir(fpath):
    """ Returns the NMS file directory from the given filepath. """
    path = Path(fpath)
    parts = path.parts
    return str(Path(*parts[:parts.index('MODELS')]))

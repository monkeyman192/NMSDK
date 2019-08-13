from pathlib import Path


def get_NMS_dir(fpath):
    """ Returns the NMS file directory from the given filepath. """
    path = Path(fpath)
    parts = path.parts
    try:
        return str(Path(*parts[:parts.index('MODELS')]))
    except ValueError:
        # In this case we may be loading a model in a custom folder.
        # We need to go back until we find a folder with a 'MODELS' folder in
        # it.
        for parent in path.parents:
            if Path(parent, 'MODELS').exists():
                return str(parent)

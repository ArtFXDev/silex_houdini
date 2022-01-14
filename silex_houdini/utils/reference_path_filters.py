import os
import pathlib

from silex_client.utils.files import is_valid_path


def skip_invalid_path(file_path):
    return not is_valid_path(str(file_path))


def skip_relative_path(file_path):
    return not file_path.is_absolute()


def skip_relative_houdini_path(file_path):
    for houdini_path in os.getenv("HOUDINI_PATH", "").split(os.pathsep):
        if not os.path.exists(houdini_path):
            continue
        if str(pathlib.Path(houdini_path)) in str(file_path):
            return True

    return False

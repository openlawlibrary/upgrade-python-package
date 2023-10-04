import os
import shutil
import stat


def remove_directory(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, onerror=_on_rm_error)
    except PermissionError:
        pass


def _on_rm_error(_func, path, _exc_info):
    """Used when calling rmtree to ensure that readonly files and folders are deleted."""
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

import logging
import os
import stat
from pathlib import Path
from sys import platform

logger = logging.getLogger(__name__)


def create_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True)
    except Exception as e:
        logger.error("Failed to create virtualenv directory: %s", e)
        raise e


def get_venv_executable(venv_path: str) -> str:
    if is_windows():
        return str(Path(venv_path, "Scripts", "python.exe").absolute())
    else:
        return str(Path(venv_path, "bin", "python3").absolute())


def is_windows() -> bool:
    return platform == "win32" or platform == "cygwin"


def on_rm_error(_func, path, _exc_info):
    """Used by when calling rmtree to ensure that readonly files and folders
    are deleted.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError as e:
        logger.debug(f"File at path {path} not found, error trace - {e}")
        return
    try:
        os.unlink(path)
    except (OSError, PermissionError) as e:
        logger.debug(f"WARNING: Failed to clean up files: {str(e)}.")
        pass

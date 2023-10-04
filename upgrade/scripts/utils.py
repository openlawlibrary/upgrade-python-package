import logging
from pathlib import Path
from sys import platform

logger = logging.getLogger(__name__)


def create_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True)
    except Exception as e:
        logger.error("Failed to create virtualenv directory: %s", e)
        raise e


def platform_specific_python_path(venv_path: str) -> str:
    if is_windows():
        return str(Path(venv_path, "Scripts", "python.exe").absolute())
    else:
        return str(Path(venv_path, "bin", "python").absolute())


def is_windows() -> bool:
    return platform == "win32" or platform == "cygwin"

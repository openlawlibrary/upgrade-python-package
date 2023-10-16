import shutil
import sys
import os
from pathlib import Path

import pytest

from upgrade.scripts.upgrade_python_package import run
from upgrade.scripts.utils import is_windows

original_executable = sys.executable

VENV_PATH = Path(__file__).parent / "venv"
REPOSITORY_WHEELS_PATH = Path(__file__).parent / "repository"


@pytest.fixture
def wheels_dir():
    return REPOSITORY_WHEELS_PATH


def pytest_configure(config):
    if is_windows():
        python_path = Path("Scripts", "python.exe")
    else:
        python_path = Path("bin", "python")
    sys.executable = str(VENV_PATH / python_path)
    sys.modules["oll"] = None


@pytest.fixture(scope="session", autouse=True)
def setup_venv():
    if VENV_PATH.exists():
        shutil.rmtree(VENV_PATH)
    os.makedirs(VENV_PATH, exist_ok=True)
    run(original_executable, "-m", "venv", str(VENV_PATH))
    yield

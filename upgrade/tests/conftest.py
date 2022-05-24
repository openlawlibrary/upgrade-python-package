import os
import shutil
import sys
import pytest
from pathlib import Path
from upgrade.scripts.upgrade_python_package import pip, run

CLOUDSMITH_KEY = os.environ.get("CLOUDSMITH_KEY")

REPOSITORY_WHEELS_PATH = Path(__file__).parent / "repository"
VENV_PATH = Path(__file__).parent / "venv"


@pytest.fixture
def wheels_dir():
    return REPOSITORY_WHEELS_PATH


@pytest.fixture(scope="session", autouse=True)
def setup_venv():
    if not VENV_PATH.exists():
        os.makedirs(VENV_PATH, exist_ok=True)
    run(sys.executable, "-m", "venv", str(VENV_PATH))
    yield
    shutil.rmtree(VENV_PATH)


@pytest.fixture
def use_pip():
    pip("install", "--upgrade", "pip")
    yield pip
    pip("uninstall", "-y", "oll-test-top-level")
    pip("uninstall", "-y", "oll-dependency1")
    pip("uninstall", "-y", "oll-dependency2")

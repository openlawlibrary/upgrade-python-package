import os
import shutil
import sys
import pytest
from pathlib import Path
from upgrade.scripts.upgrade_python_package import pip, run

CLOUDSMITH_KEY = os.environ.get("CLOUDSMITH_KEY")

REPOSITORY_WHEELS_PATH = Path(__file__).parent / "repository"
VENV_PATH = Path(__file__).parent / "venv"
original_executable = sys.executable


def pytest_configure(config):
    sys.executable = str(VENV_PATH / "Scripts" / "python.exe")
    sys.modules["oll"] = None


@pytest.fixture
def wheels_dir():
    return REPOSITORY_WHEELS_PATH


@pytest.fixture(scope="session", autouse=True)
def setup_venv():
    if not VENV_PATH.exists():
        os.makedirs(VENV_PATH, exist_ok=True)
    run(original_executable, "-m", "venv", str(VENV_PATH))
    yield
    shutil.rmtree(VENV_PATH)


@pytest.fixture(autouse=True)
def use_pip():
    pip("install", "--upgrade", "pip")
    yield pip
    pip("uninstall", "-y", "oll-test-top-level")
    pip("uninstall", "-y", "oll-dependency1")
    pip("uninstall", "-y", "oll-dependency2")


def install_local_package(dependency):
    full_dep_path = str(REPOSITORY_WHEELS_PATH / dependency)
    links_path = str(REPOSITORY_WHEELS_PATH)

    pip("install", full_dep_path, "--find-links", links_path)

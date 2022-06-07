import os
import shutil
import sys
import pytest
from mock import patch
from pathlib import Path
from upgrade.scripts.utils import is_windows
from upgrade.scripts.upgrade_python_package import pip, run

CLOUDSMITH_KEY = os.environ.get("CLOUDSMITH_KEY")

REPOSITORY_WHEELS_PATH = Path(__file__).parent / "repository"
VENV_PATH = Path(__file__).parent / "venv"
original_executable = sys.executable


def pytest_configure(config):
    if is_windows():
        python_path = Path("Scripts", "python.exe")
    else:
        python_path = Path("bin", "python")
    sys.executable = str(VENV_PATH / python_path)
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


@pytest.fixture
def constraints_dir():
    return VENV_PATH / "lib" / "site-packages"


@pytest.fixture()
def mocked_constraints_path():
    with patch(
        "upgrade.scripts.upgrade_python_package.get_constraints_file_path",
        return_value=None,
    ):
        yield


@pytest.fixture()
def mock_find_spec():
    from importlib import util

    original_find_spec = util.find_spec
    util.find_spec = lambda name, package=None: True
    yield
    util.find_spec = original_find_spec


def install_local_package(dependency, no_deps=None):
    full_dep_path = str(REPOSITORY_WHEELS_PATH / dependency)
    links_path = str(REPOSITORY_WHEELS_PATH)
    if no_deps is None:
        pip("install", full_dep_path, "--find-links", links_path)
    else:
        pip("install", full_dep_path, "--find-links", links_path, "--no-deps")

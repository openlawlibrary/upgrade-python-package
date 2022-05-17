import os
import pytest
from pathlib import Path
from upgrade.scripts.upgrade_python_package import pip

CLOUDSMITH_KEY = os.environ.get("CLOUDSMITH_KEY")
REPOSITORY_WHEELS_PATH = Path(__file__).parent / "repository"


@pytest.fixture
def wheels_dir():
    return REPOSITORY_WHEELS_PATH


@pytest.fixture
def use_pip():
    pip("install", "--upgrade", "pip")
    yield pip
    pip("uninstall", "-y", "oll-test-top-level")
    pip("uninstall", "-y", "oll-dependency1")
    pip("uninstall", "-y", "oll-dependency2")

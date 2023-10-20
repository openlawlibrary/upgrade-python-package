from functools import wraps
from pathlib import Path

import pytest
from mock import patch

from upgrade.tests.utils import remove_directory
from upgrade.scripts.upgrade_python_package import run

from upgrade.scripts.utils import get_venv_executable

from ..conftest import REPOSITORY_WHEELS_PATH, original_executable

THIS_FOLDER = Path(__file__).parent
ENVIRONMENTS_DIR = THIS_FOLDER.parent / "Environments"


def _create_venv(path, version):
    venv_name = f"oll-test-top-level~={version}"
    dependency_to_install = f"oll-test-top-level=={version}"

    venv_path = str(Path(path, venv_name))
    run(original_executable, "-m", "venv", venv_path)
    venv_executable = get_venv_executable(venv_path)
    run(
        venv_executable,
        "-m",
        "pip",
        "install",
        dependency_to_install,
        "--find-links",
        str(REPOSITORY_WHEELS_PATH),
    )


def env_fixture(make_dir=True):
    def decorator(func):
        @pytest.fixture(scope="module", autouse=True)
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                request = kwargs["request"]
                test_dir = Path(ENVIRONMENTS_DIR, Path(request.node.name).stem)
                if test_dir.is_dir():
                    remove_directory(str(test_dir.parent))
                if make_dir:
                    test_dir.mkdir(parents=True, exist_ok=True)
                yield from func(*args, **kwargs, path=str(test_dir))
            except (Exception, KeyboardInterrupt) as e:
                raise e
            finally:
                remove_directory(str(test_dir.parent))

        return wrapped

    return decorator


@env_fixture()
def envs_home(request, path=""):
    yield path


@pytest.fixture()
def mock_cloudsmith_url_valid():
    with patch("upgrade.scripts.validations.is_cloudsmith_url_valid", lambda *_,: True):
        yield


@env_fixture()
def initial_v2_0_0_venv(request, path=""):
    _create_venv(path, "2.0.0")
    yield


@env_fixture()
def initial_v2_0_1_venv(request, path=""):
    _create_venv(path, "2.0.1")
    yield

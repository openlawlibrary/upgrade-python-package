from functools import wraps
from pathlib import Path

import pytest
from mock import patch

from upgrade.tests.utils import remove_directory
from upgrade.scripts.upgrade_python_package import run

from upgrade.scripts.utils import get_venv_executable, is_windows

from ..conftest import REPOSITORY_WHEELS_PATH, original_executable

THIS_FOLDER = Path(__file__).parent
ENVIRONMENTS_DIR = THIS_FOLDER.parent / "Environments"
UPGRADE_PYTHON_PACKAGE_REPOSITORY_PATH = THIS_FOLDER.parent.parent.parent

EXPECTED_VENV_FILES = (
    ["pyvenv.cfg", "Scripts", "Lib"]
    if is_windows()
    else ["pyvenv.cfg", "bin", "lib", "include"]
)

def _create_venv(path, version, venv_name=None):
    venv_name = venv_name or f"oll-test-top-level~={version}"
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
    install_upgrade_python_package(venv_executable, None)


def env_fixture(make_dir=True):
    def decorator(func):
        @pytest.fixture(scope="module")
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                request = kwargs["request"]
                test_dir = Path(ENVIRONMENTS_DIR, Path(request.node.name).stem)
                if not test_dir.is_dir() and make_dir:
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


@pytest.fixture()
def mock_install_upgrade_python_package():
    with patch(
        "upgrade.scripts.manage_venv.install_upgrade_python_package",
        install_upgrade_python_package,
    ):
        yield


@env_fixture()
def initial_v2_0_0_venv(request, path=""):
    _create_venv(path, "2.0.0")
    yield


@env_fixture()
def initial_v2_0_1_venv(request, path=""):
    _create_venv(path, "2.0.1")
    yield


@env_fixture()
def initial_venv_without_specifier(request, path=""):
    _create_venv(path, "2.0.0", "oll-test-top-level")
    yield


@pytest.fixture()
def mock_package_index_html():
    index_html_page = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock package index html page for testing compatible dependencies script.</title>
    </head>
    <body>
    <h1>Links for oll-top-level-package</h1>
    <a>oll_test_top_level-1.0.0-py3-none-any.whl</a><br />
    <a>oll_test_top_level-2.0.0-py3-none-any.whl</a><br />
    <a>oll_test_top_level-2.0.1-py3-none-any.whl</a><br />
    <a>oll_test_top_level-2.1.0-py3-none-any.whl</a><br />
    </body>
    </html>
    """
    with patch(
        "upgrade.scripts.find_compatible_versions._get_package_index_html",
        lambda *_,: index_html_page,
    ):
        yield


def install_upgrade_python_package(venv_executable, upgrade_python_package_version):
    run(
        *([
            venv_executable,
            "-m",
            "pip",
            "install",
            "-e",
            f"{str(UPGRADE_PYTHON_PACKAGE_REPOSITORY_PATH)}",
        ])
    )

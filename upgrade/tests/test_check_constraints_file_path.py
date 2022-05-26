from pathlib import Path
from mock import patch
from upgrade.scripts.upgrade_python_package import get_constraints_file_path
from .conftest import VENV_PATH, install_local_package


def test_get_constraints_for_dependency1_from_venv_expect_constraints_exist_and_match():
    full_package_name = "oll_dependency1-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = "oll-dependency1"
    constraints_file_path = get_constraints_file_path(
        package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
    )
    expected = ["Pillow==6.2.2", "contextvars==2.4"]
    actual = Path(constraints_file_path).read_text().splitlines()

    assert len(actual) == len(expected)


def test_get_constraints_for_dependency2_from_venv_expect_constraints_exist_and_match():
    full_package_name = "oll_dependency2-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = "oll-dependency2"
    constraints_file_path = get_constraints_file_path(
        package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
    )
    expected = ["colorama==0.4.4"]
    actual = Path(constraints_file_path).read_text().splitlines()

    assert len(actual) == len(expected)


def test_get_constraints_for_top_level_package_from_venv_expect_constraints_exist_and_match():
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = "oll-test-top-level"
    constraints_file_path = get_constraints_file_path(
        package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
    )
    expected = [
        "defusedxml==0.7.1",
        "colorama==0.4.4",
        "Pillow==6.2.2",
        "contextvars==2.4",
    ]
    actual = Path(constraints_file_path).read_text().splitlines()

    assert len(actual) == len(expected)

def test_get_constraints_for_wrong_package_from_venv_expect_no_constraints_to_exist():
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = "wrong-package"
    with patch("upgrade.scripts.upgrade_python_package.constraints_file_path", None):
        constraints_file_path = get_constraints_file_path(
            package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
        )
    expected = None
    actual = constraints_file_path
    assert actual == expected

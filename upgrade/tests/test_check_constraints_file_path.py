import pytest
from pathlib import Path
from mock import patch
from upgrade.scripts.upgrade_python_package import get_constraints_file_path
from .conftest import VENV_PATH, install_local_package


@pytest.mark.parametrize(
    "package_wheel, package_name, expected_constraints",
    [
        (
            "oll_dependency1-2.0.1-py2.py3-none-any.whl",
            "oll-dependency1",
            ["mock-dependency==0.0.1"],
        ),
        (
            "oll_dependency2-2.0.1-py2.py3-none-any.whl",
            "oll-dependency2",
            ["mock-dependency==0.0.2"],
        ),
        (
            "oll_test_top_level-2.0.1-py2.py3-none-any.whl",
            "oll-test-top-level",
            [
                "dependency1==2.0.1",
                "dependency2==2.0.1",
            ],
        ),
    ],
)
def test_get_constraints_for_packages_requirements_from_venv_expect_constraints_exist_and_match(
    package_wheel, package_name, expected_constraints
):
    full_package_name = package_wheel
    install_local_package(full_package_name, no_deps=True)

    package = package_name
    cut = get_constraints_file_path
    constraints_file_path = cut(
        package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
    )
    expected = expected_constraints
    actual = Path(constraints_file_path).read_text().splitlines()

    assert len(actual) == len(expected)


def test_get_constraints_for_wrong_package_from_venv_expect_no_constraints_to_exist():
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = "wrong-package"
    cut = get_constraints_file_path
    constraints_file_path = cut(
        package, site_packages_dir=str(VENV_PATH / "lib" / "site-packages")
    )
    expected = None
    actual = constraints_file_path
    assert actual == expected

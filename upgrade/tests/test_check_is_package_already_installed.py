from upgrade.scripts.upgrade_python_package import is_package_already_installed
from upgrade.tests.conftest import install_local_package
import pytest


def test_is_package_already_installed_expect_none():
    cut = is_package_already_installed
    version = cut("oll-test-top-level")
    actual = version
    expected = None
    assert actual == expected


@pytest.mark.parametrize(
    "package_name",
    [
        ("oll-test-top-level"),
        ("oll-dependency1"),
        ("oll-dependency2"),
    ],
)
def test_is_package_already_installed_expect_package_version(package_name):
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    cut = is_package_already_installed
    version = cut(package_name)
    actual = version
    expected = "2.0.1"
    assert actual == expected
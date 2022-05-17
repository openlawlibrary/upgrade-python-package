import pytest

from upgrade.scripts.upgrade_python_package import upgrade_from_local_wheel, pip
from .conftest import CLOUDSMITH_KEY

# dependencies not installed
# pip check has broken dependencies
# install wrong oll-test-version==1.0.0
# install wrong oll-dependency==1.0.0


def test_existing_dependencies_in_vm_when_top_level_package_is_not_installed_expect_false(
    use_pip,
):
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        shell=True,
    ).splitlines()

    expected = False
    actual = any(
        "oll-test-top-level" in dependency for dependency in dependencies_from_venv
    )
    assert actual == expected


def test_upgrade_top_level_package_from_local_wheel_where_package_name_is_valid_expect_package_installed(
    wheels_dir, use_pip
):
    package_name = "oll-test-top-level"
    
    cut = upgrade_from_local_wheel
    cut(
        package_name,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
    )
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        shell=True,
    ).splitlines()

    expected = True
    actual = any(
        "oll-test-top-level" in dependency for dependency in dependencies_from_venv
    )
    assert actual == expected


def test_upgrade_top_level_package_from_local_wheel_where_package_name_does_not_exist_expect_package_install_fail(
    wheels_dir,
):
    package_name = "oll-test-top-level==1.0.0"
    
    cut = upgrade_from_local_wheel
    with pytest.raises(IndexError) as error:
        cut(
            package_name,
            skip_post_install=True,
            cloudsmith_key=CLOUDSMITH_KEY,
            wheels_path=str(wheels_dir),
        )

    expected = "list index out of range"
    actual = str(error).split("IndexError(")[1].split(",")[0].replace("'", "")
    assert actual == expected

from upgrade.scripts.upgrade_python_package import upgrade_from_local_wheel
from ..conftest import DATA_PATH
from pathlib import Path


def test_existing_dependencies_in_vm_when_expected_packages_are_not_installed_expect_false(
    use_pip,
):
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = [
        "oll-test-top-level==2.0.0",
        "oll-test-top-level==2.0.1",
        "oll-test-top-level==2.1.0",
        "oll-dependency1==2.0.0",
        "oll-dependency1==2.0.1",
        "oll-dependency2==2.0.0",
        "oll-dependency2==2.0.1",
    ]

    expected = False
    actual = any(
        dependency in expected_packages for dependency in dependencies_from_venv
    )
    assert actual == expected


def test_upgrade_local_wheel_top_level_package_2_0_0_where_package_name_is_valid_expect_package_installed(
    wheels_dir, use_pip, mocked_constraints_path
):
    package = "oll-test-top-level==2.0.0"
    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
        version="==2.0.0",
    )
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        "oll-test-top-level==2.0.0",
        "oll-dependency1==2.0.0",
        "oll-dependency2==2.0.0",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected


def test_upgrade_local_wheel_top_level_package_from_2_0_0_to_2_0_1_expect_newer_package_installed(
    wheels_dir, use_pip, mocked_constraints_path
):
    package = "oll-test-top-level==2.0.0"
    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
        version="==2.0.0",
    )

    newer_package = "oll-test-top-level==2.0.1"
    cut(
        newer_package,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
        version="==2.0.1",
    )

    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        "oll-test-top-level==2.0.1",
        "oll-dependency1==2.0.1",
        "oll-dependency2==2.0.1",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected


def test_upgrade_top_level_package_from_local_wheel_where_package_name_does_not_exist_expect_package_install_fail(
    wheels_dir, capsys
):
    package = "oll-test-top-level==1.0.0"

    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
        version="==1.0.0",
    )

    out, _ = capsys.readouterr()

    expected = "Wheel oll-test-top-level==1.0.0 not found"
    actual = out
    assert expected in actual


def test_upgrade_top_level_package_from_local_wheel_where_package_name_does_not_have_all_dependencies_locally_expect_package_install_fail(
    wheels_dir, capsys
):
    package = "oll-test-top-level==2.1.0"

    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(wheels_dir),
        version="==2.1.0",
    )

    out, _ = capsys.readouterr()

    expected = "Failed to install wheel"
    actual = out
    assert expected in actual


def test_upgrade_local_wheel_test_constraints_flag(
    use_pip
):
    package = "oll-test-top-level==2.0.2"
    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(Path(DATA_PATH) / "test_constraints_flag"),
        constraints_path=str(Path(DATA_PATH) / "test_constraints_flag/constraints.txt"),
        version="~=2.0.2",
    )
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        "oll-test-top-level==2.0.2",
        "oll-dependency1==2.0.0",
        "oll-dependency2==2.0.0",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected
    
def test_upgrade_local_wheel_test_no_constraints_flag(
    use_pip
):
    package = "oll-test-top-level==2.0.2"
    cut = upgrade_from_local_wheel
    cut(
        package,
        skip_post_install=True,
        wheels_path=str(Path(DATA_PATH) / "test_constraints_flag"),
        version="~=2.0.2",
    )
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        "oll-test-top-level==2.0.2",
        "oll-dependency1==2.0.2",
        "oll-dependency2==2.0.2",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected
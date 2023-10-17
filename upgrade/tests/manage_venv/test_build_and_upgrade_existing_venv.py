from mock import patch
from pathlib import Path

from upgrade.scripts.manage_venv import (
    build_and_upgrade_venv,
    venv_pip,
    _get_venv_executable,
)


def test_build_and_upgrade_venv_where_v2_0_0_venv_exists_and_auto_upgrade_is_enabled_expect_venv_upgraded_to_v2_0_1(
    initial_v2_0_0_venv, envs_home, wheels_dir, mock_cloudsmith_url_valid
):
    dependency_to_install = "oll-test-top-level~=2.0.0"
    expected_installed_version = "2.0.1"

    cut = build_and_upgrade_venv

    with patch(
        "upgrade.scripts.manage_venv.determine_compatible_upgrade_version",
        lambda *_,: expected_installed_version,
    ):
        cut(
            dependency_to_install,
            envs_home,
            auto_upgrade=True,
            cloudsmith_url="",
            wheels_path=str(wheels_dir),
            update_from_local_wheels=True,
        )

    venv_path = Path(envs_home, dependency_to_install)
    venv_executable = _get_venv_executable(venv_path)

    venv_pip(venv_executable, "check")

    dependencies_from_venv = venv_pip(
        venv_executable,
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        f"oll-test-top-level=={expected_installed_version}",
        f"oll-dependency1=={expected_installed_version}",
        f"oll-dependency2=={expected_installed_version}",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected


def test_build_and_upgrade_venv_where_v2_0_1_venv_exists_and_auto_upgrade_is_disabled_expect_venv_unchanged(
    initial_v2_0_1_venv, envs_home, wheels_dir, mock_cloudsmith_url_valid, capfd
):
    dependency_to_install = "oll-test-top-level~=2.0.1"
    expected_installed_version = "2.0.1"

    cut = build_and_upgrade_venv

    with patch(
        "upgrade.scripts.manage_venv.determine_compatible_upgrade_version",
        lambda *_,: expected_installed_version,
    ):
        cut(
            dependency_to_install,
            envs_home,
            auto_upgrade=False,
            cloudsmith_url="",
            wheels_path=str(wheels_dir),
            update_from_local_wheels=True,
        )
    out, _ = capfd.readouterr() # TODO: read from logs since capture does not work from venv

    expected = "Requirements did not change. Returning venv executable."
    actual = out

    assert expected in actual


def test_build_and_upgrade_venv_where_v2_0_1_venv_exists_and_auto_upgrade_is_enabled_expect_venv_unchanged_and_on_same_version(
    initial_v2_0_1_venv, envs_home, wheels_dir, mock_cloudsmith_url_valid, capfd
):
    dependency_to_install = "oll-test-top-level~=2.0.1"
    expected_installed_version = "2.0.1"

    cut = build_and_upgrade_venv

    with patch(
        "upgrade.scripts.manage_venv.determine_compatible_upgrade_version",
        lambda *_,: expected_installed_version,
    ):
        cut(
            dependency_to_install,
            envs_home,
            auto_upgrade=True,
            cloudsmith_url="",
            wheels_path=str(wheels_dir),
            update_from_local_wheels=True,
        )

    venv_path = Path(envs_home, dependency_to_install)
    venv_executable = _get_venv_executable(venv_path)

    venv_pip(venv_executable, "check")

    dependencies_from_venv = venv_pip(
        venv_executable,
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        f"oll-test-top-level=={expected_installed_version}",
        f"oll-dependency1=={expected_installed_version}",
        f"oll-dependency2=={expected_installed_version}",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected

from pathlib import Path

from upgrade.scripts.manage_venv import build_and_upgrade_venv
from upgrade.scripts.upgrade_python_package import pip
from upgrade.scripts.utils import get_venv_executable
from upgrade.tests.manage_venv.conftest import EXPECTED_VENV_FILES
from upgrade.tests.manage_venv.test_utils import assert_dependencies_installed_in_venv

VENV_SUFFIX = "_green"


def test_build_and_upgrade_venv_where_blue_green_deployment_is_enabled_and_venv_2_0_0_exists_expect_green_venv_built_and_upgraded_to_v2_0_1(
    initial_v2_0_0_venv,
    envs_home,
    wheels_dir,
    mock_cloudsmith_url_valid,
):
    dependency_to_install = "oll-test-top-level~=2.0.0"
    cut = build_and_upgrade_venv
    cut(
        dependency_to_install,
        envs_home,
        auto_upgrade=True,
        wheels_path=str(wheels_dir),
        update_from_local_wheels=True,
        blue_green_deployment=True,
        log_location=Path(envs_home, "manage_venv.log"),
    )

    _assert_green_venv(
        envs_home,
        dependency_to_install,
        expected_installed_version="2.0.1",
    )
    _assert_blue_venv(
        envs_home, dependency_to_install, expected_installed_version="2.0.0"
    )


def test_build_and_upgrade_venv_where_blue_green_deployment_is_enabled_and_venv_2_0_1_exists_expect_green_venv_built_and_unchanged(
    initial_v2_0_1_venv,
    envs_home,
    wheels_dir,
    mock_cloudsmith_url_valid,
):
    dependency_to_install = "oll-test-top-level~=2.0.1"
    cut = build_and_upgrade_venv
    cut(
        dependency_to_install,
        envs_home,
        auto_upgrade=True,
        wheels_path=str(wheels_dir),
        update_from_local_wheels=True,
        blue_green_deployment=True,
        log_location=Path(envs_home, "manage_venv.log"),
    )

    _assert_green_venv(
        envs_home,
        dependency_to_install,
        expected_installed_version="2.0.1",
    )
    _assert_blue_venv(
        envs_home, dependency_to_install, expected_installed_version="2.0.1"
    )


def _assert_green_venv(envs_home, dependency_to_install, expected_installed_version):
    venv_path = Path(envs_home, dependency_to_install + VENV_SUFFIX)
    venv_executable = get_venv_executable(venv_path)

    assert_dependencies_installed_in_venv(venv_executable, expected_installed_version)

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_VENV_FILES:
        assert Path(venv_path, file).exists()

    pip("check", py_executable=venv_executable)


def _assert_blue_venv(envs_home, dependency_to_install, expected_installed_version):
    blue_venv = Path(envs_home, dependency_to_install)
    venv_executable = get_venv_executable(blue_venv)

    assert_dependencies_installed_in_venv(venv_executable, expected_installed_version)

    pip("check", py_executable=venv_executable)

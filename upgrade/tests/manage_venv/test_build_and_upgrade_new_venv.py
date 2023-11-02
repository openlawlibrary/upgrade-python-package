from pathlib import Path

import pytest

from upgrade.scripts.manage_venv import build_and_upgrade_venv
from upgrade.scripts.utils import get_venv_executable
from upgrade.tests.manage_venv.conftest import EXPECTED_VENV_FILES
from upgrade.tests.manage_venv.test_utils import assert_dependencies_installed_in_venv


@pytest.mark.parametrize(
    "dependency_to_install, expected_installed_version",
    [
        ("oll-test-top-level==2.0.0", "2.0.0"),
        ("oll-test-top-level==2.0.1", "2.0.1"),
        ("oll-test-top-level~=2.0.0", "2.0.1"),
        ("oll-test-top-level~=2.0.1", "2.0.1"),
    ],
)
def test_build_and_upgrade_venv_where_venv_did_not_exist_and_auto_upgrade_is_disabled_expect_venv_created_and_upgraded(
    dependency_to_install,
    expected_installed_version,
    envs_home,
    wheels_dir,
    mock_cloudsmith_url_valid,
    mock_install_upgrade_python_package,
):
    cut = build_and_upgrade_venv
    cut(
        dependency_to_install,
        envs_home,
        auto_upgrade=False,
        wheels_path=str(wheels_dir),
        update_from_local_wheels=True,
        log_location=Path(envs_home, "manage_venv.log"),
    )
    venv_path = Path(envs_home, dependency_to_install)

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_VENV_FILES:
        assert Path(venv_path, file).exists()

    venv_executable = get_venv_executable(venv_path)

    assert_dependencies_installed_in_venv(venv_executable, expected_installed_version)

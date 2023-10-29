from pathlib import Path

import pytest

from upgrade.scripts.manage_venv import build_and_upgrade_venv
from upgrade.scripts.upgrade_python_package import pip
from upgrade.scripts.utils import get_venv_executable, is_windows

EXPECTED_VENV_FILES = (
    ["pyvenv.cfg", "Scripts", "Lib"]
    if is_windows()
    else ["pyvenv.cfg", "bin", "lib", "include"]
)


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
        blue_green_deployment=False,
        log_location=Path(envs_home, "manage_venv.log"),
    )
    venv_path = Path(envs_home, dependency_to_install)

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_VENV_FILES:
        assert Path(venv_path, file).exists()

    venv_executable = get_venv_executable(venv_path)

    dependencies_from_venv = pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        py_executable=venv_executable,
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

import pytest
from mock import patch

from upgrade.scripts.utils import is_windows
from upgrade.scripts.manage_venv import (
    build_and_upgrade_venv,
    venv_pip,
    _get_venv_executable,
)
from pathlib import Path

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
):
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
    venv_path = Path(envs_home, dependency_to_install)

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_VENV_FILES:
        assert Path(venv_path, file).exists()

    venv_executable = _get_venv_executable(venv_path)

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

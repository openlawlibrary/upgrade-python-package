import pytest
import mock

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
        ("oll-test-top-level==2.0.1", "2.0.1"),
        # ("oll-test-top-level~=2.0.1", "2.0.1"), # TODO: make top-level 2.0.2 into 2.1.0 
        # ("oll-test-top-level==3.0.1", "3.0.1"), 
    ],
)
def test_create_venv_when_not_exists_expect_created(
    dependency_to_install, expected_installed_version, envs_home, wheels_dir
):
    cut = build_and_upgrade_venv

    with mock.patch(
        "upgrade.scripts.manage_venv.determine_compatible_upgrade_version",
        lambda *_,: expected_installed_version,
    ), mock.patch(
        "upgrade.scripts.validations.is_cloudsmith_url_valid", lambda *_,: True
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

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_VENV_FILES:
        assert Path(venv_path, file).exists()

    breakpoint()
    venv_executable = _get_venv_executable(venv_path)

    dependencies_from_venv = venv_pip(
        venv_executable,
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    assert f"oll-test-top-level=={expected_installed_version}" in dependencies_from_venv
    assert f"oll-dependency1=={expected_installed_version}" in dependencies_from_venv
    assert f"oll-dependency2=={expected_installed_version}" in dependencies_from_venv

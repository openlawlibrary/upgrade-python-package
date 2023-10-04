import pytest

from upgrade.scripts.utils import is_windows
from upgrade.scripts.manage_venv import build_and_upgrade_venv
from pathlib import Path

EXPECTED_FILES = (
    ["pyvenv.cfg", "Scripts", "Lib"]
    if is_windows()
    else ["pyvenv.cfg", "bin", "lib", "include"]
)


@pytest.mark.parametrize(
    "requirements_file_content",
    [
        ("oll-test-top-level~=2.0.0"),
        ("oll-test-top-level~=2.0.1"),
        ("oll-test-top-level==3.0.1"),
    ],
)
def test_create_venv_when_not_exists_expect_created(
    requirements_file_content, envs_home
):
    cut = build_and_upgrade_venv
    cut(
        requirements_file_content,
        envs_home,
        auto_upgrade=False,
        cloudsmith_url=None,
    )

    venv_path = Path(envs_home, requirements_file_content)

    assert venv_path.exists()
    assert venv_path.is_dir()

    for file in EXPECTED_FILES:
        assert Path(venv_path, file).exists()
    # confirm expected dependencies exist in venv

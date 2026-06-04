"""Characterization test for the venv consistency check.

`_check_venv_consistent` wraps a `pip check` (and, after the inspection migration, a
`uv pip check`) of the venv: it raises `UpgradeError` when the venv has broken
dependencies and returns quietly when it is consistent. The failure path was not
otherwise covered, so we pin the behavior here against a real venv. This is
swap-stable: it exercises the observable contract, not which tool runs the check.
"""

import sys
from pathlib import Path

import pytest

from upgrade.scripts.exceptions import UpgradeError
from upgrade.scripts.manage_venv import _check_venv_consistent
from upgrade.scripts.requirements import to_requirements_obj
from upgrade.scripts.utils import get_uv_executable, get_venv_executable, run

from ..conftest import WHEELS_DIR

REQUIREMENTS = "oll-test-top-level~=2.0.0"


def _wheel(name):
    return str(Path(WHEELS_DIR) / name)


def test_check_venv_consistent_raises_on_broken_then_passes_when_repaired(tmp_path):
    uv_bin = get_uv_executable()
    env_path = tmp_path / "env"
    run(uv_bin, "venv", "--seed", "--python", sys.executable, str(env_path))
    py_executable = get_venv_executable(str(env_path))
    requirements_obj = to_requirements_obj(REQUIREMENTS)

    # Install the top-level package without its deps -> venv is inconsistent.
    run(
        uv_bin,
        "pip",
        "install",
        "-p",
        py_executable,
        "--no-deps",
        _wheel("oll_test_top_level-2.0.1-py2.py3-none-any.whl"),
    )

    with pytest.raises(UpgradeError):
        _check_venv_consistent(requirements_obj, py_executable)

    # Install the missing pinned deps -> venv becomes consistent.
    run(
        uv_bin,
        "pip",
        "install",
        "-p",
        py_executable,
        "--no-deps",
        _wheel("oll_dependency1-2.0.1-py2.py3-none-any.whl"),
        _wheel("oll_dependency2-2.0.1-py2.py3-none-any.whl"),
    )

    # Should not raise.
    _check_venv_consistent(requirements_obj, py_executable)

"""Tests for the installer: uv is the sole installer, with no pip fallback.

`installer` builds a `uv pip <subcommand> -p <python> ...` command and runs it. There
is no longer a pip fallback: a missing uv is a hard error. The dedicated `pip()`
helper remains for read-only inspection and is exercised elsewhere.
"""

import pytest

from upgrade.scripts import utils


def test_installer_builds_uv_pip_command(monkeypatch):
    calls = []
    monkeypatch.setattr(utils, "get_uv_executable", lambda: "/fake/uv")
    monkeypatch.setattr(utils, "run", lambda *cmd, **kw: calls.append(cmd) or "")

    utils.installer(
        "install",
        "pkg==1.0.0",
        "--no-deps",
        py_executable="/venv/bin/python",
    )

    assert calls == [
        ("/fake/uv", "pip", "install", "-p", "/venv/bin/python", "pkg==1.0.0", "--no-deps")
    ]


def test_installer_requires_a_subcommand(monkeypatch):
    monkeypatch.setattr(utils, "get_uv_executable", lambda: "/fake/uv")

    with pytest.raises(ValueError):
        utils.installer()


def test_installer_errors_when_uv_missing(monkeypatch):
    monkeypatch.setattr(utils, "get_uv_executable", lambda: None)

    with pytest.raises(RuntimeError):
        utils.installer("install", "pkg==1.0.0")

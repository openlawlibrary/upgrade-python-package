"""Tests for locating the uv binary used by the installer.

`get_uv_executable` prefers the binary bundled with the `uv` PyPI package (a declared
dependency) and falls back to a `uv` on PATH only when the package is not importable.
"""

import sys
import types
from pathlib import Path

from upgrade.scripts import utils


def test_get_uv_executable_prefers_bundled_binary():
    uv_bin = utils.get_uv_executable()

    assert uv_bin is not None
    assert Path(uv_bin).name.startswith("uv")


def test_get_uv_executable_falls_back_to_path_when_package_missing(monkeypatch):
    fake_uv = types.ModuleType("uv")

    def _missing():
        raise FileNotFoundError("bundled binary not found")

    fake_uv.find_uv_bin = _missing
    monkeypatch.setitem(sys.modules, "uv", fake_uv)
    monkeypatch.setattr(
        utils.shutil,
        "which",
        lambda name: "/usr/local/bin/uv" if name == "uv" else None,
    )

    assert utils.get_uv_executable() == "/usr/local/bin/uv"

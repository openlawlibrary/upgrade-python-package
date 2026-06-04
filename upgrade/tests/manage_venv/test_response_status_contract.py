"""Characterization tests for the machine-readable status output contract.

`manage_venv` and `find_compatible_versions` print a single JSON object to stdout
that downstream consumers (Ansible cron jobs) parse to decide what to do next. The
exact `responseStatus` values are part of the tool's public contract, so we pin them
here before the uv migration changes anything underneath. These tests stub out the
heavy lifting (real venvs / index scraping) on purpose: they characterize the output
shape, not the install behavior, and stay valid across the pip->uv swap.
"""

import json

import pytest

from upgrade.scripts import find_compatible_versions as fcv
from upgrade.scripts import manage_venv as mv

REQUIREMENTS = "oll-test-top-level~=2.0.0"


def _printed_json(capsys):
    out, _ = capsys.readouterr()
    # The status object is the last JSON line printed in the finally block.
    last_line = [line for line in out.splitlines() if line.strip()][-1]
    return json.loads(last_line)


def test_find_compatible_versions_when_upgrade_available_prints_available(
    monkeypatch, capsys
):
    monkeypatch.setattr(fcv, "is_package_already_installed", lambda *a, **k: "2.0.0")
    monkeypatch.setattr(fcv, "get_compatible_version", lambda *a, **k: "2.0.1")

    fcv.find_compatible_versions(
        venv_path="/does/not/matter",
        requirements=REQUIREMENTS,
        requirements_file=None,
        test=True,
    )

    assert _printed_json(capsys) == {"responseStatus": "AVAILABLE"}


def test_find_compatible_versions_when_no_upgrade_prints_at_latest_version(
    monkeypatch, capsys
):
    monkeypatch.setattr(fcv, "is_package_already_installed", lambda *a, **k: "2.0.1")
    monkeypatch.setattr(fcv, "get_compatible_version", lambda *a, **k: None)

    fcv.find_compatible_versions(
        venv_path="/does/not/matter",
        requirements=REQUIREMENTS,
        requirements_file=None,
        test=True,
    )

    assert _printed_json(capsys) == {"responseStatus": "AT_LATEST_VERSION"}


def test_find_compatible_versions_on_failure_prints_error_and_reraises(
    monkeypatch, capsys
):
    monkeypatch.setattr(fcv, "is_package_already_installed", lambda *a, **k: "2.0.0")

    def _boom(*_a, **_k):
        raise RuntimeError("index unreachable")

    monkeypatch.setattr(fcv, "get_compatible_version", _boom)

    with pytest.raises(Exception):
        fcv.find_compatible_versions(
            venv_path="/does/not/matter",
            requirements=REQUIREMENTS,
            requirements_file=None,
            test=True,
        )

    assert _printed_json(capsys) == {"responseStatus": "ERROR"}


def test_manage_venv_on_success_prints_upgraded(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(mv, "build_and_upgrade_venv", lambda *a, **k: ("py", None))

    mv.manage_venv(
        envs_home=str(tmp_path),
        requirements=REQUIREMENTS,
        test=True,
    )

    assert _printed_json(capsys) == {"responseStatus": "UPGRADED"}


def test_manage_venv_on_failure_prints_error_and_reraises(monkeypatch, capsys, tmp_path):
    def _boom(*_a, **_k):
        raise RuntimeError("install failed")

    monkeypatch.setattr(mv, "build_and_upgrade_venv", _boom)

    with pytest.raises(Exception):
        mv.manage_venv(
            envs_home=str(tmp_path),
            requirements=REQUIREMENTS,
            test=True,
        )

    assert _printed_json(capsys) == {"responseStatus": "ERROR"}

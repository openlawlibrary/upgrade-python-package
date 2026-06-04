"""Characterization test for the `upgrade --format-output` JSON contract.

When run with `format_output=True`, `upgrade_python_package` prints a single JSON
object of the form `{"success": <bool>, "responseOutput": <str>}`. Consumers rely on
this shape to detect success and surface output, so we pin it before the uv migration.
The actual upgrade work is stubbed: this characterizes the output shape, not install
behavior, and stays valid across the pip->uv swap.
"""

import json

from upgrade.scripts import upgrade_python_package as upp


def _printed_json(capsys):
    out, _ = capsys.readouterr()
    last_line = [line for line in out.splitlines() if line.strip()][-1]
    return json.loads(last_line)


def test_format_output_reports_success_shape(monkeypatch, capsys):
    monkeypatch.setattr(upp, "is_package_already_installed", lambda *a, **k: "2.0.1")
    monkeypatch.setattr(
        upp, "upgrade_and_run", lambda *a, **k: ("upgraded", "install output")
    )

    upp.upgrade_python_package(
        "oll-test-top-level",
        test=True,
        format_output=True,
    )

    assert _printed_json(capsys) == {
        "success": True,
        "responseOutput": "install output",
    }


def test_format_output_reports_unchanged_as_unsuccessful(monkeypatch, capsys):
    monkeypatch.setattr(upp, "is_package_already_installed", lambda *a, **k: "2.0.1")
    monkeypatch.setattr(upp, "upgrade_and_run", lambda *a, **k: ("unchanged", ""))

    upp.upgrade_python_package(
        "oll-test-top-level",
        test=True,
        format_output=True,
    )

    assert _printed_json(capsys) == {"success": False, "responseOutput": ""}

"""Characterization test for the --no-deps vs --update-all install contract.

This is the load-bearing behavior behind the rolling / auto-pickup release model:

- Default mode (update_all=False) installs the named package with `--no-deps`, so a
  newly published version of *our* package flows out without disturbing the rest of
  the resolved dependency set.
- `--update-all` mode omits `--no-deps`, letting the resolver touch dependencies too.

We pin this at the argument-construction level (capturing what `install_wheel` passes
to `installer`) rather than via a real install: the test packages pin their deps with
`==`, so a real `--no-deps` upgrade would trip the consistency-repair path and obscure
the flag we want to observe. The decision lives in `install_wheel`, above `installer`,
so this test stays valid when `installer` switches from pip to uv underneath.
"""

from upgrade.scripts import upgrade_python_package as upp


def _capture_installer_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(upp, "installer", lambda *a, **k: calls.append(a) or "")
    # `pip check` and the installed-version lookup are irrelevant to arg construction.
    monkeypatch.setattr(upp, "uv_pip", lambda *a, **k: "")
    monkeypatch.setattr(upp, "is_package_already_installed", lambda *a, **k: None)
    return calls


def test_default_install_passes_no_deps(monkeypatch):
    calls = _capture_installer_calls(monkeypatch)

    upp.install_wheel("oll-test-top-level", version_cmd="==2.0.1", update_all=False)

    assert calls, "expected installer to be invoked"
    primary_install = calls[0]
    assert "--no-deps" in primary_install
    assert "oll-test-top-level==2.0.1" in primary_install


def test_update_all_install_omits_no_deps(monkeypatch):
    calls = _capture_installer_calls(monkeypatch)

    upp.install_wheel("oll-test-top-level", version_cmd="==2.0.1", update_all=True)

    assert calls, "expected installer to be invoked"
    primary_install = calls[0]
    assert "--no-deps" not in primary_install
    assert "oll-test-top-level==2.0.1" in primary_install

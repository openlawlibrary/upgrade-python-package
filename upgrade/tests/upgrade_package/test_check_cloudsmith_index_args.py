import subprocess

from upgrade.scripts import upgrade_python_package as script


CLOUDSMITH_URL = "https://dl.cloudsmith.io/public/openlawlibrary/test/simple/"


def test_install_with_constraints_prefers_cloudsmith_with_pypi_fallback(monkeypatch):
    calls = []

    monkeypatch.setattr(
        script,
        "installer",
        lambda *args: calls.append(args) or "",
    )

    script.install_with_constraints(
        wheel_path="pkg==1.0.0",
        constraints_file_path="/tmp/constraints.txt",
        cloudsmith_url=CLOUDSMITH_URL,
    )

    assert calls == [
        (
            "install",
            "pkg==1.0.0",
            "-c",
            "/tmp/constraints.txt",
            "--extra-index-url",
            CLOUDSMITH_URL,
            "--index-url",
            script.PYPI_SIMPLE_URL,
        )
    ]


def test_install_wheel_prefers_cloudsmith_with_pypi_fallback(monkeypatch):
    calls = []

    monkeypatch.setattr(
        script,
        "installer",
        lambda *args: calls.append(args) or "",
    )
    monkeypatch.setattr(script, "pip", lambda *args: "")
    monkeypatch.setattr(script, "is_package_already_installed", lambda package: None)

    script.install_wheel(
        package_name="pkg",
        cloudsmith_url=CLOUDSMITH_URL,
        version_cmd="==1.0.0",
    )

    assert calls == [
        (
            "install",
            "pkg==1.0.0",
            "--extra-index-url",
            CLOUDSMITH_URL,
            "--index-url",
            script.PYPI_SIMPLE_URL,
            "--no-deps",
        )
    ]


def test_install_wheel_reinstall_prefers_cloudsmith_with_pypi_fallback(monkeypatch):
    calls = []

    def fake_installer(*args):
        calls.append(args)
        return ""

    def fake_pip(*args):
        raise subprocess.CalledProcessError(1, list(args))

    def fail_install_with_constraints(*args, **kwargs):
        raise RuntimeError("constraints failed")

    monkeypatch.setattr(script, "installer", fake_installer)
    monkeypatch.setattr(script, "pip", fake_pip)
    monkeypatch.setattr(
        script,
        "install_with_constraints",
        fail_install_with_constraints,
    )
    monkeypatch.setattr(script, "is_package_already_installed", lambda package: "1.0.0")

    script.install_wheel(
        package_name="pkg",
        cloudsmith_url=CLOUDSMITH_URL,
        version_cmd="==2.0.0",
    )

    assert calls == [
        (
            "install",
            "pkg==2.0.0",
            "--extra-index-url",
            CLOUDSMITH_URL,
            "--index-url",
            script.PYPI_SIMPLE_URL,
            "--no-deps",
        ),
        (
            "install",
            "--no-deps",
            "pkg==1.0.0",
            "--extra-index-url",
            CLOUDSMITH_URL,
            "--index-url",
            script.PYPI_SIMPLE_URL,
        ),
    ]

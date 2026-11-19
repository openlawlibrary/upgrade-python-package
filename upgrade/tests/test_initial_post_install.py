import logging
import subprocess

import pytest

from upgrade.scripts import upgrade_python_package as upp


def test_upgrade_python_package_where_package_has_extra_expect_initial_post_install_runs(
    tmp_path, monkeypatch, caplog
):
    package_dir = tmp_path / "site"
    module_dir = package_dir / "post_install_probe"
    module_dir.mkdir(parents=True)
    marker = tmp_path / "ran"
    (module_dir / "__init__.py").write_text("")
    (module_dir / "__main__.py").write_text(
        f"open({str(marker)!r}, 'w').close()\n"
    )
    monkeypatch.syspath_prepend(str(package_dir))
    monkeypatch.setenv("PYTHONPATH", str(package_dir))

    flag_dir = tmp_path / "flags"
    flag_dir.mkdir()
    flag = flag_dir / "post_install_probe_run_post_install"
    flag.touch()
    monkeypatch.setattr(upp, "POST_INSTALL_FLAG_DIR", str(flag_dir))
    caplog.set_level("INFO")

    cut = upp.upgrade_python_package
    cut(
        "post-install-probe[development]",
        should_run_initial_post_install=True,
        test=True,
    )

    assert marker.exists()
    assert not flag.exists()
    assert "result=post_install_ran" in caplog.text


def test_upgrade_python_package_where_module_is_missing_expect_flag_kept(
    tmp_path, monkeypatch, caplog
):
    flag_dir = tmp_path / "flags"
    flag_dir.mkdir()
    flag = flag_dir / "missing_probe_run_post_install"
    flag.touch()
    monkeypatch.setattr(upp, "POST_INSTALL_FLAG_DIR", str(flag_dir))
    caplog.set_level("INFO")

    cut = upp.upgrade_python_package
    cut("missing-probe", should_run_initial_post_install=True, test=True)

    assert flag.exists()
    assert "result=no_module" in caplog.text


def test_upgrade_python_package_where_flag_is_missing_expect_flag_path_and_no_flag_result(
    tmp_path, monkeypatch, caplog
):
    monkeypatch.setattr(upp, "POST_INSTALL_FLAG_DIR", str(tmp_path))
    caplog.set_level("INFO")

    cut = upp.upgrade_python_package
    cut("missing-probe", should_run_initial_post_install=True, test=True)

    flag_path = str(tmp_path / "missing_probe_run_post_install")
    assert any(
        r.levelno == logging.INFO and flag_path in r.getMessage() for r in caplog.records
    )
    assert "result=no_flag" in caplog.text


def test_upgrade_python_package_where_initial_post_install_fails_expect_slack_notice_and_flag_kept(
    tmp_path, monkeypatch
):
    package_dir = tmp_path / "site"
    module_dir = package_dir / "failing_probe"
    module_dir.mkdir(parents=True)
    (module_dir / "__init__.py").write_text("")
    (module_dir / "__main__.py").write_text("raise SystemExit(1)\n")
    monkeypatch.syspath_prepend(str(package_dir))
    monkeypatch.setenv("PYTHONPATH", str(package_dir))

    flag_dir = tmp_path / "flags"
    flag_dir.mkdir()
    flag = flag_dir / "failing_probe_run_post_install"
    flag.touch()
    monkeypatch.setattr(upp, "POST_INSTALL_FLAG_DIR", str(flag_dir))

    webhook = "https://hooks.slack.invalid/services/T0/B0/probe"
    monkeypatch.setenv("SLACK_WEBHOOK_URL", webhook)
    notices = []
    monkeypatch.setattr(
        upp,
        "send_upgrade_notification",
        lambda header, cloudsmith_url, slack_webhook_url: notices.append(
            (header, slack_webhook_url)
        ),
    )

    cut = upp.upgrade_python_package
    with pytest.raises(subprocess.CalledProcessError):
        cut("failing-probe[development]", should_run_initial_post_install=True, test=True)

    assert notices == [("Failed to run module failing_probe", webhook)]
    assert flag.exists()

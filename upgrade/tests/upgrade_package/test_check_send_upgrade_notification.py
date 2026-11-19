import traceback

import pytest

from upgrade.scripts import upgrade_python_package as script
from upgrade.scripts.exceptions import SlackError

SECRET = "xoxb-secret-part"


def test_send_upgrade_notification_where_slack_post_fails_expect_webhook_secret_not_logged(
    monkeypatch, caplog
):
    monkeypatch.setattr(script, "get_server_metadata", lambda: "user@127.0.0.1")

    cut = script.send_upgrade_notification
    with pytest.raises(SlackError) as raised:
        cut(
            "Failed to upgrade package pkg",
            "https://dl.cloudsmith.io/token/openlawlibrary/repo/python/index/",
            f"hooks.slack.com/services/T0/B0/{SECRET}",
        )

    logged_by_caller = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert SECRET not in caplog.text
    assert SECRET not in logged_by_caller

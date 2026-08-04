import os

import pytest
from packaging.version import Version

from upgrade.scripts.find_compatible_versions import get_compatible_upgrade_versions
from upgrade.scripts.requirements import to_requirements_obj

# Set to a live openlawlibrary/development Cloudsmith index URL (with the entitlement
# token embedded, e.g. https://dl.cloudsmith.io/<token>/openlawlibrary/development/python/index/)
# to run this against the real index instead of a mocked one. Skipped otherwise, since it
# needs real network access and a real credential this repo doesn't store.
CLOUDSMITH_DEV_URL = os.environ.get("CLOUDSMITH_DEV_URL_TEST")

pytestmark = pytest.mark.skipif(
    not CLOUDSMITH_DEV_URL,
    reason="CLOUDSMITH_DEV_URL_TEST is not set - export a live development Cloudsmith "
    "index URL to exercise this against the real index",
)


def test_get_compatible_upgrade_versions_where_dev_channel_expect_prereleases_included():
    cut = get_compatible_upgrade_versions

    requirements_obj = to_requirements_obj("oll-cls~=2.21")
    versions = cut(requirements_obj, CLOUDSMITH_DEV_URL)

    assert versions, "expected at least one dev version from the live development index"
    assert any(Version(v) > Version("2.21.6.dev184") for v in versions), (
        "expected a version newer than the known-stale 2.21.6.dev184 to be present - "
        "if this fails, prereleases are being filtered out again (the bug this test guards)"
    )

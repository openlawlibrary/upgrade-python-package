"""Characterization tests for development-index detection.

`is_development_cloudsmith` decides whether prereleases are allowed and how runs are
labelled. Development mode is determined from the explicit Cloudsmith URL (which
carries the literal "development" for our development index). There is no ambient
config sniffing: uv ignores pip's configuration, so a `None` URL is simply "not
development". These tests pin that contract and are stable across the migration that
removes the old pip-config fallback (the `pip` stub makes the None case deterministic
on the pre-migration code regardless of the host's ambient pip config).
"""

from upgrade.scripts import utils

DEV_URL = "https://dl.cloudsmith.io/abc/openlawlibrary/development/python/simple/"
PROD_URL = "https://dl.cloudsmith.io/abc/openlawlibrary/stable/python/simple/"


def test_development_url_is_detected():
    assert utils.is_development_cloudsmith(DEV_URL) is True


def test_production_url_is_not_development():
    assert utils.is_development_cloudsmith(PROD_URL) is False


def test_no_url_is_not_development(monkeypatch):
    # No explicit URL -> not development. Stubbing pip keeps this deterministic on the
    # pre-migration code (empty config); after migration pip is not consulted at all.
    monkeypatch.setattr(utils, "pip", lambda *a, **k: "")
    assert utils.is_development_cloudsmith(None) is False

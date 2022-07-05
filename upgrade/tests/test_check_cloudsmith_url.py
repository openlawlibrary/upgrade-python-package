from upgrade.scripts.upgrade_python_package import is_cloudsmith_url_valid
from contextlib import nullcontext as does_not_raise
from .conftest import CLOUDSMITH_URL
import pytest


def test_check_cloudsmith_url_where_url_is_invalid_expect_error():
    cut = is_cloudsmith_url_valid
    invalid_cloudsmith_url = (
        "https://dl.cloudsmith.io/test/test/test/"
    )
    with pytest.raises(Exception) as e:
        cut(invalid_cloudsmith_url)
    assert (
        f"Failed to reach cloudsmith. Provided invalid URL: {invalid_cloudsmith_url}"
        in str(e)
    )


@pytest.mark.skipif(not CLOUDSMITH_URL, reason="Valid cloudsmith url is not set.")
def test_check_cloudsmith_url_where_url_is_valid_expect_success():
    cut = is_cloudsmith_url_valid
    with does_not_raise() as e:
        cut(CLOUDSMITH_URL)
    expected = None
    actual = e
    assert actual == expected

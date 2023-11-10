import pytest
from pip._vendor.packaging.specifiers import SpecifierSet

from upgrade.scripts.requirements import filter_versions


@pytest.mark.parametrize(
    "specifier_set, available_versions, expected",
    [
        (SpecifierSet("==2.0.0"), ["2.0.0", "2.0.1", "2.1.0"], ["2.0.0"]),
        (SpecifierSet("~=2.0.0"), ["2.0.0", "2.0.1", "2.1.0"], ["2.0.0", "2.0.1"]),
        (SpecifierSet("~=2.0.1"), ["2.0.0", "2.0.1", "2.1.0"], ["2.0.1"]),
        (SpecifierSet("~=2.0.1"), ["2.1.0", "2.0.1", "2.0.0"], ["2.0.1"]),
        (SpecifierSet("==2.1.0"), ["2.0.0", "2.0.1", "2.1.0"], ["2.1.0"]),
        (SpecifierSet("~=2.1.0"), ["2.0.0", "2.0.1", "2.1.0"], ["2.1.0"]),
        (SpecifierSet("~=2.1.1"), ["2.0.0", "2.0.1", "2.1.0"], []),
        (SpecifierSet("~=3.3.3"), ["2.0.0", "2.0.1", "2.1.0"], []),
    ],
)
def test_filter_versions_with_different_specifiers(
    specifier_set, available_versions, expected
):
    cut = filter_versions

    actual = cut(specifier_set, available_versions)

    assert actual == expected

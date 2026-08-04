import pytest
from packaging.specifiers import SpecifierSet

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


def test_filter_versions_where_channel_is_dev_only_expect_none_found_by_default():
    cut = filter_versions

    actual = cut(SpecifierSet("~=2.21"), ["2.21.6.dev184", "2.21.6.dev200"])

    assert actual == []


def test_filter_versions_where_channel_is_dev_only_and_prereleases_true_expect_all_found():
    cut = filter_versions

    actual = cut(
        SpecifierSet("~=2.21"), ["2.21.6.dev184", "2.21.6.dev200"], prereleases=True
    )

    assert actual == ["2.21.6.dev184", "2.21.6.dev200"]

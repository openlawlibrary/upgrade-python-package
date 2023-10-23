from pathlib import Path

from upgrade.scripts.find_compatible_versions import get_compatible_version
from upgrade.scripts.requirements import to_requirements_obj


def test_get_compatible_version_where_current_installed_version_is_2_0_0_and_compatible_upgrade_version_is_2_0_1_expect_compatible_upgrade_version_returned(
    initial_v2_0_0_venv,
    envs_home,
    mock_package_index_html,
):
    cut = get_compatible_version

    requirements = "oll-test-top-level~=2.0.0"
    venv_path = Path(envs_home, requirements)

    actual = cut(
        requirements_obj=to_requirements_obj(requirements),
        venv_path=str(venv_path),
    )
    expected = "2.0.1"

    assert actual == expected


def test_get_compatible_version_where_current_installed_version_is_2_0_1_and_compatible_upgrade_version_is_2_0_1_expect_no_compatible_upgrade_version(
    initial_v2_0_1_venv,
    envs_home,
    mock_package_index_html,
):
    cut = get_compatible_version

    requirements = "oll-test-top-level~=2.0.1"
    venv_path = Path(envs_home, requirements)

    actual = cut(
        requirements_obj=to_requirements_obj(requirements),
        venv_path=str(venv_path),
    )
    expected = None

    assert actual == expected


def test_get_compatible_version_where_current_installed_version_is_2_0_0_and_from_venv_without_specifier_and_compatible_upgrade_version_is_2_1_0_expect_compatible_upgrade_version_returned(
    initial_venv_without_specifier,
    envs_home,
    mock_package_index_html,
):
    cut = get_compatible_version

    requirements = "oll-test-top-level"
    venv_path = Path(envs_home, requirements)

    actual = cut(
        requirements_obj=to_requirements_obj(requirements),
        venv_path=str(venv_path),
    )
    expected = "2.1.0"

    assert actual == expected

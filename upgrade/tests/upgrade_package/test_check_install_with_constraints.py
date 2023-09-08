import pytest
import subprocess
from upgrade.scripts.upgrade_python_package import install_with_constraints

from .conftest import install_local_package


@pytest.mark.parametrize(
    "version",
    [
        ("2.0.0"),
        ("2.0.1"),
    ],
)
def test_install_top_level_package_2_0_1_with_constraints_expect_success(
    version,
    wheels_dir,
    constraints_dir,
    use_pip,
):
    full_package_name = f"oll_test_top_level-{version}-py2.py3-none-any.whl"
    install_local_package(full_package_name, no_deps=True)

    package = f"oll-test-top-level=={version}"
    cut = install_with_constraints
    cut(
        wheel_path=package,
        constraints_file_path=str(
            constraints_dir / "oll_test_top_level" / "constraints.txt"
        ),
        local=True,
        wheels_dir=str(wheels_dir),
    )
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    expected_packages = {
        f"oll-test-top-level=={version}",
        f"oll-dependency1=={version}",
        f"oll-dependency2=={version}",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected


def test_install_top_level_package_2_0_2_without_constraints_where_dependencies_do_not_exist_expect_error(
    wheels_dir, capsys
):
    package = "oll-test-top-level==2.0.2"
    cut = install_with_constraints
    with pytest.raises(Exception):
        cut(
            wheel_path=package,
            constraints_file_path=None,
            local=True,
            wheels_dir=str(wheels_dir),
        )
    out, _ = capsys.readouterr()

    expected = f"Failed to install wheel {package}"
    actual = out
    assert expected in actual

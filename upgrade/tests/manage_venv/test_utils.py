from upgrade.scripts.upgrade_python_package import pip


def assert_dependencies_installed_in_venv(venv_executable, expected_version):
    dependencies_from_venv = pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        py_executable=venv_executable,
    ).splitlines()

    expected_packages = {
        f"oll-test-top-level=={expected_version}",
        f"oll-dependency1=={expected_version}",
        f"oll-dependency2=={expected_version}",
    }
    actual_packages = set(dependencies_from_venv)

    expected = True
    actual = expected_packages.issubset(actual_packages)
    assert actual == expected

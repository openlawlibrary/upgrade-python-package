from upgrade.scripts.upgrade_python_package import upgrade_from_local_wheel


def test_upgrade_local_wheels_top_level_package_from_2_0_0_to_2_0_1_expect_success(
    wheels_dir, use_pip, capfd, mocked_constraints_path, mock_find_spec
):
    package = "oll-test-top-level==2.0.0"
    upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
        version="==2.0.0",
    )

    use_pip("check")
    out, _ = capfd.readouterr()

    assert "No broken requirements found" in out
    assert f"Wheel {package} not found" not in out
    # module should run
    assert "Hello from main" in out

    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()
    assert "oll-test-top-level==2.0.0" in dependencies_from_venv
    assert "oll-dependency1==2.0.0" in dependencies_from_venv
    assert "oll-dependency2==2.0.0" in dependencies_from_venv

    # now upgrade to newer version
    package = "oll-test-top-level==2.0.1"
    success, _ = upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
        version="==2.0.1",
    )

    assert success

    use_pip("check")
    out, _ = capfd.readouterr()

    assert "No broken requirements found" in out
    assert "Hello from main" in out
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()
    assert "oll-test-top-level==2.0.0" not in dependencies_from_venv
    assert "oll-dependency1==2.0.0" not in dependencies_from_venv
    assert "oll-dependency2==2.0.0" not in dependencies_from_venv
    assert "oll-test-top-level==2.0.1" in dependencies_from_venv
    assert "oll-dependency1==2.0.1" in dependencies_from_venv
    assert "oll-dependency2==2.0.1" in dependencies_from_venv


def test_upgrade_local_wheels_top_level_package_from_2_0_1_to_2_1_0_expect_error_and_revert_to_2_0_1(
    wheels_dir, use_pip, capfd, mocked_constraints_path
):
    package = "oll-test-top-level==2.0.1"
    upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
        version="==2.0.1",
    )

    use_pip("check")
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()
    assert "oll-test-top-level==2.0.1" in dependencies_from_venv
    assert "oll-dependency1==2.0.1" in dependencies_from_venv
    assert "oll-dependency2==2.0.1" in dependencies_from_venv

    package = "oll-test-top-level==2.1.0"
    upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
        version="==2.1.0",
    )

    out, _ = capfd.readouterr()

    assert "Failed to install wheel" in out
    assert "Successfully uninstalled oll-test-top-level-2.1.0" in out
    assert "Successfully installed oll-test-top-level-2.0.1" in out

    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
    ).splitlines()

    assert "oll-test-top-level==2.1.0" not in dependencies_from_venv
    assert "oll-test-top-level==2.0.1" in dependencies_from_venv
    use_pip("check")

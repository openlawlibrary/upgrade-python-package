from upgrade.scripts.upgrade_python_package import upgrade_from_local_wheel


def test_upgrade_local_wheel_top_level_package(wheels_dir, use_pip, capfd):
    package = "oll-test-top-level==2.0.0"
    upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
    )
    out, _ = capfd.readouterr()
    #pip("check") has error output 
    assert "oll-test-top-level 2.0.0 requires oll-dependency1, which is not installed." in out
    assert "oll-test-top-level 2.0.0 requires oll-dependency2, which is not installed." in out
    assert f'Wheel {package} not found' not in out
    #module should run
    assert "Hello from main" in out

    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        shell=True,
    ).splitlines()
    assert "oll-test-top-level==2.0.0" in dependencies_from_venv
    assert "oll-dependency1==2.0.0" in dependencies_from_venv
    assert "oll-dependency2==2.0.0" in dependencies_from_venv

    #now upgrade to newer version
    package = "oll-test-top-level==2.0.1"
    upgrade_from_local_wheel(
        package,
        skip_post_install=False,
        wheels_path=str(wheels_dir),
    )
    out, _ = capfd.readouterr() 
    assert "oll-test-top-level 2.0.0 requires oll-dependency1, which is not installed." not in out
    assert "oll-test-top-level 2.0.0 requires oll-dependency2, which is not installed." not in out
    assert "oll-test-top-level 2.0.1 requires oll-dependency1, which is not installed." in out
    assert "oll-test-top-level 2.0.1 requires oll-dependency2, which is not installed." in out

    assert "Hello from main" in out
    dependencies_from_venv = use_pip(
        "list",
        "--format=freeze",
        "--exclude-editable",
        shell=True,
    ).splitlines()
    assert "oll-test-top-level==2.0.0" not in dependencies_from_venv
    assert "oll-dependency1==2.0.0" not in dependencies_from_venv
    assert "oll-dependency2==2.0.0" not in dependencies_from_venv
    assert "oll-test-top-level==2.0.1" in dependencies_from_venv
    assert "oll-dependency1==2.0.1" in dependencies_from_venv
    assert "oll-dependency2==2.0.1" in dependencies_from_venv

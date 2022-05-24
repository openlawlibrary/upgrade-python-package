from upgrade.scripts.upgrade_python_package import try_running_module
from .conftest import install_local_package


def test_try_running_module_expect_success_and_print(capsys):
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    module_name = "oll_test_top_level"
    cut = try_running_module
    cut(module_name)
    out, _ = capsys.readouterr()

    expected = "Hello from main"
    actual = out
    assert expected in actual


def test_try_running_module_where_wrong_package_is_installed_expect_error_in_print(
    capsys,
):
    full_package_name = "oll_dependency2-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    module_name = "oll_dependency2"
    cut = try_running_module
    cut(module_name)
    out, _ = capsys.readouterr()

    expected = "Hello dependency 2"
    actual = out
    assert expected not in actual

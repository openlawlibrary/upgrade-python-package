from mock import patch
from upgrade.scripts.upgrade_python_package import try_running_module
from .conftest import install_local_package


def test_try_running_module_expect_success_and_print(capsys, mock_find_spec):
    full_package_name = "oll_test_top_level-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)
    out, _ = capsys.readouterr()
    module_name = "oll_test_top_level"
    cut = try_running_module
    cut(module_name)
    out, _ = capsys.readouterr()
    expected = "Hello from main"
    actual = out
    assert expected in actual


def test_try_running_module_where_module_name_is_a_wrong_directory_expect_error(capsys):
    full_package_name = "oll_test_top_level-2.0.0-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    module_name = "oll"
    cut = try_running_module
    cut(module_name)

    out, _ = capsys.readouterr()
    expected = "No module named oll"
    actual = out
    assert expected in actual


def test_try_running_module_where_package_is_not_a_module_expect_error(capsys):
    full_package_name = "oll_dependency1-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    module_name = "dependency1"
    cut = try_running_module
    cut(module_name)

    out, _ = capsys.readouterr()
    expected = "No module named dependency1"
    actual = out
    assert expected in actual


def test_try_running_module_where_another_package_is_not_a_module_expect_error(capsys):
    full_package_name = "oll_dependency2-2.0.1-py2.py3-none-any.whl"
    install_local_package(full_package_name)

    module_name = "oll"
    cut = try_running_module
    cut(module_name)

    out, _ = capsys.readouterr()
    expected = "No module named oll"
    actual = out
    assert expected in actual
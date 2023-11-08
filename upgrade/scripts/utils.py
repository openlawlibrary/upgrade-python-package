import json
import logging
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from sys import platform

from upgrade.scripts.exceptions import PipFormatDecodeFailed

logger = logging.getLogger(__name__)


development_url_re = re.compile(r"([^']+development[^']+)")
development_index_re = re.compile(r"install.index-url='([^']+development[^']+)'")


def create_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True)
    except Exception as e:
        logger.error("Failed to create virtualenv directory: %s", e)
        raise e


def get_venv_executable(venv_path: str) -> str:
    if is_windows():
        return str(Path(venv_path, "Scripts", "python.exe").absolute())
    else:
        return str(Path(venv_path, "bin", "python3").absolute())


def is_windows() -> bool:
    return platform == "win32" or platform == "cygwin"


def is_development_cloudsmith(cloudsmith_url):
    if cloudsmith_url is not None:
        return development_url_re.search(cloudsmith_url) is not None
    try:
        pip_config = pip("config", "list")
    except subprocess.CalledProcessError as e:
        logging.warning("config command not found.")
        pip_config = ""

    return development_index_re.search(pip_config) is not None


def on_rm_error(_func, path, _exc_info):
    """Used by when calling rmtree to ensure that readonly files and folders
    are deleted.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError as e:
        logger.debug(f"File at path {path} not found, error trace - {e}")
        return
    try:
        os.unlink(path)
    except (OSError, PermissionError) as e:
        logger.debug(f"WARNING: Failed to clean up files: {str(e)}.")
        pass


def pip(*args, **kwargs):
    """
    Run pip using the python executable used to run this function
    """
    return run_python_module("pip", *args, **kwargs)


def run(*command, **kwargs):
    """Run a command and return its output"""
    if len(command) == 1 and isinstance(command[0], str):
        command = command[0].split()
    print(*command)
    command = [word.format(**os.environ) for word in command]
    try:
        options = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=kwargs.pop("check", True),
            universal_newlines=True,
        )
        options.update(kwargs)
        completed = subprocess.run(command, **options)
    except subprocess.CalledProcessError as err:
        logging.warning('Error occurred while running command "%s"', *command)
        if err.stdout:
            print(err.stdout)
            logging.warning(err.stdout)
        if err.stderr:
            print(err.stderr)
            logging.warning(err.stderr)
        print(
            'Command "{}" returned non-zero exit status {}'.format(
                " ".join(command), err.returncode
            )
        )
        logging.warning(
            'Command "%s" returned non-zero exit status %s',
            " ".join(command),
            err.returncode,
        )
        raise err
    if completed.stdout:
        print(completed.stdout)
        logging.info("Completed. Output: %s", completed.stdout)
    return completed.stdout.rstrip() if completed.returncode == 0 else None


def run_python_module(module_name, *args, **kwargs):
    """
    Run a python module using the python executable used to run this function
    """
    if not args and not kwargs:
        # check for arguments stored in an environment variable UPDATE_MODULE_NAME
        var_name = f"UPDATE_{module_name.upper()}"
        args = tuple(os.environ.get(var_name, "").split())
    logging.info("running %s python module", module_name)
    py_executable = kwargs.pop("py_executable", sys.executable)
    try:
        return run(*((py_executable, "-m", module_name) + args), **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Error occurred while running module %s: %s", module_name, str(e))
        raise e


def is_package_already_installed(package, py_executable=None):
    if py_executable is None:
        py_executable = sys.executable

    results = pip("list", "--format", "json", py_executable=py_executable)
    try:
        decoder = json.JSONDecoder()
        parsed_results, _ = decoder.raw_decode(results)
    except json.JSONDecodeError:
        msg = "Error occurred while decoding pip list to json"
        logging.error(msg)
        raise PipFormatDecodeFailed(msg)
    package = package.split("==")[0] if "==" in package else package
    found_package = [
        (element["name"], element["version"])
        for element in parsed_results
        if element["name"] == package
    ]
    if found_package:
        _, version = found_package.pop()
        return version
    logging.info(f"Package not found: ${package}")
    return None

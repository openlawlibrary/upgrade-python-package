import json
import logging
import os
import re
import shutil
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
    logging.debug(
        'Running command executable="%s" arg_count=%s', command[0], len(command) - 1
    )
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
        logging.warning('Error occurred while running command "%s"', " ".join(command))
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
        logging.debug("Completed. Output: %s", completed.stdout)
    return completed.stdout.rstrip() if completed.returncode == 0 else None


def format_exception(exc: Exception) -> str:
    """Return a readable error string, including subprocess output when present."""
    if isinstance(exc, subprocess.CalledProcessError):
        command = exc.cmd
        if isinstance(command, (list, tuple)):
            command = " ".join(str(part) for part in command)

        parts = [f'Command "{command}" returned non-zero exit status {exc.returncode}.']

        output = exc.stdout if exc.stdout is not None else exc.output
        output = output.strip() if isinstance(output, str) else output
        stderr = exc.stderr.strip() if isinstance(exc.stderr, str) else exc.stderr

        if output:
            parts.append(f"Output:\n{output}")
        if stderr and stderr != output:
            parts.append(f"Stderr:\n{stderr}")

        return "\n".join(parts)

    return str(exc)


def get_uv_executable():
    """Locate the uv binary.

    Prefer the binary bundled with the `uv` PyPI package, which is a declared
    dependency and therefore present wherever this tool is installed. Fall back to a
    `uv` found on PATH for environments where the package is not yet importable.
    Returns None if neither is available.
    """
    try:
        from uv import find_uv_bin

        return find_uv_bin()
    except (ImportError, FileNotFoundError):
        return shutil.which("uv")


def installer(*args, **kwargs):
    """Install/uninstall packages using uv.

    uv is the sole installer: it is a declared dependency located via
    `get_uv_executable()`, so every install/uninstall operation goes through it. The
    dedicated `pip()` helper is retained only for read-only inspection where callers
    rely on pip output (`pip list --format json`, `pip check`). A missing uv is a
    hard error rather than a silent pip fallback, which previously caused uv-vs-pip
    divergence across machines.
    """
    if not args:
        raise ValueError("installer() requires a uv pip subcommand")
    py_executable = kwargs.pop("py_executable", None) or sys.executable
    uv_bin = get_uv_executable()
    if uv_bin is None:
        raise RuntimeError(
            "uv executable not found; the 'uv' package is a required dependency"
        )

    subcommand = str(args[0])
    cmd = [uv_bin, "pip", subcommand, "-p", str(py_executable)]
    cmd.extend([str(arg) for arg in args[1:]])
    return run(*cmd, **kwargs)


def run_python_module(module_name, *args, **kwargs):
    """
    Run a python module using the python executable used to run this function
    """
    if not args and not kwargs:
        # check for arguments stored in an environment variable UPDATE_MODULE_NAME
        var_name = f"UPDATE_{module_name.upper()}"
        args = tuple(os.environ.get(var_name, "").split())
    logging.debug("running %s python module", module_name)
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

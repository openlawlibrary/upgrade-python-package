import subprocess
import sys
import os
import re
import logging
import glob
import argparse
from importlib import util
from pathlib import Path
import site


DIST_INFO_RE_FORMAT = r"^{package_name}-.+\.dist-info$"
PYTHON_VERSION_RE = r"^python3.[0-9]+$"


def upgrade_and_run(
    package_install_cmd, force, skip_post_install, version, cloudsmith_url=None, *args
):
    """
    If the package needs to be upgraded upgrade it and then
    run the package (`python -m <package_name>`).
    We strip brackets before running the packag in case you
    are installing something like `pip package[env]`.
    Any post-install/post-upgrade functionality should go in
    that top-level module. Any args passed to this function
    are passed on to the package script.
    Restart uwsgi application that is the same name as package.
    """
    package_name = package_install_cmd.split("[", 1)[0]
    if version is not None:
        logging.info(
            "Trying to install version %s of package %s", version, package_name
        )
        was_updated = attempt_to_install_version(
            package_install_cmd, version, cloudsmith_url
        )
    else:
        logging.info('Trying to upgrade "%s" package.', package_name)
        was_updated = attempt_upgrade(package_install_cmd)
    if not skip_post_install and (was_updated or force):
        module_name = package_name.replace("-", "_")
        try_running_module(module_name, *args)


def get_constraints_file_path(package_name, site_packages_dir=None):
    """
    Find the path to the constraints file from site-packages.
    """

    # get site-packages dir of current venv
    try:
        import oll

        # get oll path with pathlib
        oll_path = Path(oll.__file__).parent
        # get constraints.txt file path from oll_path
        constraints_file_path = oll_path / "constraints.txt"
        if constraints_file_path.exists():
            return str(constraints_file_path)
        raise ImportError
    except (ImportError, AttributeError):
        site_packages_dir = (
            Path(site_packages_dir)
            if site_packages_dir
            else Path(site.getsitepackages()[1])
        )

        package_name = package_name.replace("-", "_")
        constraints_file_path = site_packages_dir / package_name / "constraints.txt"
        if os.path.exists(constraints_file_path):
            return str(constraints_file_path)

    return None



def install_with_constraints(
    wheel_path, constraints_file_path, cloudsmith_url=None, local=False, wheels_dir=None
):
    """
    Install a wheel with constraints. If there is no constraints file, then install it without constraints.
    """
    try:
        if constraints_file_path:
            logging.info("Installing wheel with constraints %s", wheel_path)
            if cloudsmith_url:
                pip(
                    "install",
                    wheel_path,
                    "-c",
                    constraints_file_path,
                    "--extra-index-url",
                    "https://pypi.python.org/simple/",
                    "--index-url",
                    cloudsmith_url,
                )
            elif local:
                pip(
                    "install",
                    wheel_path,
                    "-c",
                    constraints_file_path,
                    "--find-links",
                    wheels_dir,
                )
            else:
                pip("install", wheel_path, "-c", constraints_file_path)
        else:
            # install without constraints for backwards compatibility
            logging.info(
                "No constraints.txt found. Installing wheel %s without constraints.txt",
                wheel_path,
            )
            if cloudsmith_url:
                pip(
                    "install",
                    wheel_path,
                    "--extra-index-url",
                    "https://pypi.python.org/simple/",
                    "--index-url",
                    cloudsmith_url,
                )
            elif local:
                pip("install", wheel_path, "--find-links", wheels_dir)
            else:
                pip("install", wheel_path)
    except Exception:
        logging.error("Failed to install wheel %s", wheel_path)
        print("Failed to install wheel %s" % wheel_path)
        raise


def install_wheel(package_name, cloudsmith_url=None, local=False, wheels_path=None):
    """
    Try to install a wheel with no-deps and if there are no broken dependencies, pass it.
    If there are broken dependencies, try to install it with constraints.
    """
    if local:
        package_name, extra = split_package_name_and_extra(package_name)
        try:
            wheel = glob.glob(
                f'{wheels_path}/{package_name.replace("-", "_").replace("==","-")}*.whl'
            )[0]
        except IndexError:
            print(f"Wheel {package_name} not found")
            raise
        to_install = wheel + extra
    else:
        to_install = package_name
    try:
        # check if the wheel is already installed
        wheel_metadata = pip("show", package_name.split("==")[0])
        # if wheel is already installed, save version to revert upgrade if constraints fail
        version = wheel_metadata.split("Version:")[1].split("\n")[0].strip()
    except Exception:
        # wheel is not installed
        version = None

    if cloudsmith_url is not None:
        pip(
            "install",
            "--no-deps",
            to_install,
            "--index-url",
            cloudsmith_url,
        )
    else:
        pip("install", "--no-deps", to_install)

    try:
        pip("check")
    except:
        # try to install with constraints
        constraints_file_path = get_constraints_file_path(package_name)
        try:
            install_with_constraints(
                package_name, constraints_file_path, cloudsmith_url, local, wheels_path
            )
        except:
            # if install with constraints fails or the installation caused broken dependencies
            # revert back to old package version
            if version is not None:
                package_name = package_name.split("==")[0]
                if local:
                    pip(
                        "install",
                        "--no-deps",
                        f"{package_name}=={version}",
                        "--find-links",
                        wheels_path,
                    )
                else:
                    pip("install", "--no-deps", f"{package_name}=={version}")
            else:
                raise


def upgrade_from_local_wheel(
    package_install_cmd, skip_post_install, *args, cloudsmith_url=None, wheels_path=None
):
    package_name, _ = split_package_name_and_extra(package_install_cmd)
    try:
        install_wheel(
            package_install_cmd, cloudsmith_url, local=True, wheels_path=wheels_path
        )
    except Exception:
        raise
    if not skip_post_install:
        module_name = package_name.replace("-", "_").split("==")[0]
        try_running_module(module_name, *args)


development_index_re = re.compile(r"install.index-url='([^']+development[^']+)'")


def attempt_to_install_version(package_install_cmd, version, cloudsmith_url=None):
    """
    attempt to install a specific version of the given package
    """
    try:
        resp = ""
        # constraints_file_path = install_with_no_deps(f'{package_install_cmd}=={version}')
        # install_with_constraints(f'{package_install_cmd}=={version}', constraints_file_path)
        install_wheel(f"{package_install_cmd}=={version}", cloudsmith_url)
    except Exception:
        logging.info(f"Could not find {package_install_cmd} {version}")
        print(f"Could not find {package_install_cmd} {version}")
        return False
    return "Successfully installed" in resp


def attempt_upgrade(package_install_cmd):
    """
    attempt to upgrade a packgage with the given package_install_cmd.
    return True if it was upgraded.
    """
    pip_config = pip("config", "list")
    pip_args = []
    match = development_index_re.search(pip_config)
    if match:
        pip_args.append("--pre")

    resp = pip("install", *pip_args, "--upgrade", package_install_cmd)
    was_upgraded = "Requirement already up-to-date" not in resp
    if was_upgraded:
        logging.info('"%s" package was upgraded.', package_install_cmd)
    else:
        logging.info('"%s" package was already up-to-date.', package_install_cmd)
    return was_upgraded


def reload_uwsgi_app(package_name):
    uwsgi_vassals_dir = "/etc/uwsgi/vassals"
    logging.info("Reloading uwsgi app %s", package_name)
    ini_file_path = os.path.join(uwsgi_vassals_dir, f"{package_name}.ini")
    if not os.path.isfile(ini_file_path):
        logging.debug("%s is not a uwsgi app", package_name)
        return
    logging.debug(
        "%s is a uwsgi app. Modifying the ini file %s", package_name, ini_file_path
    )
    run("touch", "--no-dereference", ini_file_path)


def pip(*args, **kwargs):
    """
    Run pip using the python executable used to run this function
    """
    return run_python_module("pip", *args, **kwargs)


def run_initial_post_install(package_name, *args):
    file_name = f'{package_name.replace("-", "_")}_run_post_install'
    file_path = os.path.join("/opt/var", file_name)
    run_post_install = os.path.isfile(file_path)
    if run_post_install:
        logging.info("Running initial post install of package %s", package_name)
        module_name = package_name.replace("-", "_")
        try_running_module(module_name, *args)
        # delete the file to avoid running post install again
        os.remove(file_path)


def run_python_module(module_name, *args, **kwargs):
    """
    Run a python module using the python executable used to run this function
    """
    if not args and not kwargs:
        # check for arguments stored in an environemtn variable UPDATE_MODULE_NAME
        var_name = f"UPDATE_{module_name.upper()}"
        args = tuple(os.environ.get(var_name, "").split())
    logging.info("running %s python module", module_name)
    try:
        return run(*((sys.executable, "-m", module_name) + args), **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Error occurred while running module %s: %s", module_name, str(e))
        raise e


def run_module_and_reload_uwsgi_app(module_name, *args):
    run_python_module(module_name, *args)
    package_name = module_name.replace("_", "-")
    reload_uwsgi_app(package_name)


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
            check=True,
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


def split_package_name_and_extra(package_install_cmd):
    extra_start = package_install_cmd.find("[")
    if extra_start != -1:
        package_name = package_install_cmd[:extra_start]
        extra = package_install_cmd[extra_start:]
    else:
        extra = ""
        package_name = package_install_cmd
    return package_name, extra


def try_running_module(wheel, *args):
    file_name = os.path.basename(wheel)
    module_name = file_name.split("-", 1)[0]
    # don't try running the module if it does not exists
    # prevents errors from being printed in case of trying
    # to run e.g. oll-core or oll-partners
    if util.find_spec(module_name) and util.find_spec(".__main__", package=module_name):
        run_module_and_reload_uwsgi_app(module_name, *args)
    else:
        logging.info("No module named %s", module_name)
        print(f"No module named {module_name}")


parser = argparse.ArgumentParser()
parser.add_argument(
    "--test",
    action="store_true",
    help="Determines whether log messages will be output to stdout "
    + "or written to a log file",
)
parser.add_argument(
    "--skip-post-install",
    action="store_true",
    help="Skip post install even if the new wheels were installed",
)
parser.add_argument(
    "--update-from-local-wheels",
    action="store_true",
    help="Determines whether to install packages from local wheels, which "
    + "are expected to be in /vagrat/wheels directory",
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Used to specify that post-install scripts should be run even if "
    + "the package was not updated",
)
parser.add_argument(
    "--run-initial-post-install",
    action="store_true",
    help="Used to run post install of the given package after initial startup",
)
parser.add_argument(
    "--version",
    action="store",
    type=str,
    default=None,
    help="Package version to install",
)
parser.add_argument(
    "--cloudsmith-url",
    action="store",
    type=str,
    default=None,
    help="Cloudsmith URL with an API key necessary during local testing.",
)
parser.add_argument(
    "--wheels-path",
    action="store",
    type=str,
    default=None,
    help="Path to the directory containing the wheels.",
)
parser.add_argument(
    "package",
    nargs="?",
    help="Specifies what needs to be updated. E.g. oll-publish-server or "
    + "oll-draft-server[development]",
)
parser.add_argument(
    "vars",
    nargs="*",
    help="A list of optional arugments needed by the post-install script of the "
    + "specified package. If no arguments are provided, it is checked if there "
    + "are environment variables which store the needed values."
    + 'These variables should be named "UPDATE_PACKAGE_NAME"',
)
parser.add_argument("--log-location", help="Specifies where to store the log file")
if __name__ == "__main__":
    parsed_args = parser.parse_args()
    if parsed_args.test:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    else:
        log_location = parsed_args.log_location or "/var/log/upgrade_python_package.log"
        logging.basicConfig(
            filename=log_location,
            level=logging.WARNING,
            format="%(asctime)s %(message)s",
        )
    wheels_path = parsed_args.wheels_path or "/vagrant/wheels"
    if parsed_args.update_from_local_wheels:
        if parsed_args.package:
            upgrade_from_local_wheel(
                parsed_args.package,
                parsed_args.skip_post_install,
                wheels_path=wheels_path,
                cloudsmith_url=parsed_args.cloudsmith_url,
                *parsed_args.vars,
            )
    elif parsed_args.run_initial_post_install:
        run_initial_post_install(parsed_args.package, *parsed_args.vars)
    else:
        upgrade_and_run(
            parsed_args.package,
            parsed_args.force,
            parsed_args.skip_post_install,
            parsed_args.version,
            cloudsmith_url=parsed_args.cloudsmith_url,
            *parsed_args.vars,
        )

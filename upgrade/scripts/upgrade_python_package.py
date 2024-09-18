import argparse
import glob
import json
import logging
import os
import site
from importlib import util
from pathlib import Path

from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.utils import parse_wheel_filename

from upgrade.scripts.exceptions import PipFormatDecodeFailed
from upgrade.scripts.requirements import filter_versions
from upgrade.scripts.slack import send_slack_notification
from upgrade.scripts.utils import (
    is_development_cloudsmith,
    is_package_already_installed,
    pip,
    run,
    run_python_module,
)
from upgrade.scripts.validations import is_cloudsmith_url_valid

DIST_INFO_RE_FORMAT = r"^{package_name}-.+\.dist-info$"
PYTHON_VERSION_RE = r"^python3.[0-9]+$"


def upgrade_and_run(
    package_install_cmd,
    force,
    skip_post_install,
    version,
    cloudsmith_url=None,
    update_all=False,
    slack_webhook_url=None,
    constraints_path = None,
    *args,
):
    """
    If the package needs to be upgraded upgrade it and then
    run the package (`python -m <package_name>`).
    We strip brackets before running the package in case you
    are installing something like `pip package[env]`.
    Any post-install/post-upgrade functionality should go in
    that top-level module. Any args passed to this function
    are passed on to the package script.
    Restart uwsgi application that is the same name as package.
    """
    package_name = package_install_cmd.split("[", 1)[0]
    was_updated = False
    response_err = ""
    if version is not None:
        logging.info(
            "Trying to install version %s of package %s", version, package_name
        )
        was_updated, response_err = attempt_to_install_version(
            package_install_cmd,
            version,
            cloudsmith_url,
            update_all,
            slack_webhook_url,
            constraints_path,
        )
    else:
        logging.info('Trying to upgrade "%s" package.', package_name)
        was_updated, response_err = attempt_upgrade(
            package_install_cmd,
            cloudsmith_url,
            update_all,
            slack_webhook_url,
            constraints_path,
            *args,
        )
    if not skip_post_install and (was_updated or force):
        module_name = package_name.replace("-", "_")
        try_running_module(
            module_name,
            cloudsmith_url=cloudsmith_url,
            slack_webhook_url=slack_webhook_url,
            *args,
        )
    return was_updated, response_err


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
    except (TypeError, ImportError, AttributeError):
        if site_packages_dir:
            site_packages_dir = Path(site_packages_dir)
        else:
            try:
                site_packages_dir = Path(site.getsitepackages()[1])
            except IndexError:
                site_packages_dir = Path(site.getsitepackages()[0])
        package_name = package_name.replace("-", "_")
        constraints_file_path = site_packages_dir / package_name / "constraints.txt"
        if os.path.exists(constraints_file_path):
            return str(constraints_file_path)

    return None


def get_log_file_path():
    """Get the path to the log file."""
    try:
        return Path(logging.getLoggerClass().root.handlers[0].baseFilename)
    except (AttributeError, IndexError):
        return None


def get_server_metadata():
    """Get the server metadata in format user@ipaddress"""
    user = os.getlogin()

    def _get_public_ip_address():
        import urllib.request

        return urllib.request.urlopen("https://ident.me").read().decode("utf8")

    def _get_private_ip_address():
        import socket

        return socket.gethostbyname(socket.gethostname())

    try:
        ip = _get_public_ip_address()
    except Exception:
        ip = _get_private_ip_address()

    return f"{user}@{ip}"


def install_with_constraints(
    wheel_path,
    constraints_file_path,
    cloudsmith_url=None,
    local=False,
    wheels_dir=None,
    *args,
):
    """
    Install a wheel with constraints. If there is no constraints file, then install it without constraints.
    """
    resp = None
    try:
        install_args = [
            "install",
            wheel_path,
        ]
        if constraints_file_path:
            logging.info("Installing wheel with constraints %s", wheel_path)
            install_args.extend(["-c", constraints_file_path])
        else:
            # install without constraints for backwards compatibility
            logging.info(
                "No constraints.txt found. Installing wheel %s without constraints.txt",
                wheel_path,
            )
        if local:
            install_args.extend(
                [
                    "--find-links",
                    wheels_dir,
                ]
            )
        if cloudsmith_url:
            install_args.extend(
                [
                    "--extra-index-url",
                    "https://pypi.python.org/simple/",
                    "--index-url",
                    cloudsmith_url,
                ]
            )
        install_args.extend(args)
        resp = pip(*install_args)
        return resp
    except Exception:
        logging.error("Failed to install wheel %s", wheel_path)
        print("Failed to install wheel %s" % wheel_path)
        raise


def install_wheel(
    package_name,
    cloudsmith_url=None,
    local=False,
    wheels_path=None,
    version_cmd=None,
    update_all=False,
    slack_webhook_url=None,
    constraints_path=None,
    *args,
):
    """
    Try to install a wheel with no-deps and if there are no broken dependencies, pass it.
    If there are broken dependencies, try to install it with constraints.
    """
    resp = ""
    package_name, extra = split_package_name_and_extra(package_name)
    if local:
        try:
            wheel_paths = sorted(
                glob.glob(
                    f'{wheels_path}/{package_name.replace("-", "_").replace("==","-")}*.whl'
                )
            )
            wheel_names = [Path(path).name for path in wheel_paths]
            parsed_wheel_versions = [
                str(parse_wheel_filename(wheel_name)[1]) for wheel_name in wheel_names
            ]
            wheel_mapping = {k: v for (k, v) in zip(parsed_wheel_versions, wheel_paths)}
            if version_cmd is not None:
                versions = filter_versions(
                    SpecifierSet(version_cmd), parsed_wheel_versions
                )
                wheel = wheel_mapping.get(versions[-1])
            else:
                wheel = parsed_wheel_versions[-1]
        except IndexError:
            print(f"Wheel {package_name} not found")
            raise
        except Exception as e:
            print(f"Failed to install wheel {package_name} due to error: {e}")
            raise
        to_install = wheel + extra
    else:
        to_install = (
            package_name + version_cmd
            if version_cmd is not None
            else package_name + extra
        )

    try:
        version = is_package_already_installed(package_name)
    except PipFormatDecodeFailed as e:
        msg = (
            "Something went wrong with pip.\n"
            "You should consider upgrading your pip by running: 'python -m pip install --upgrade pip' command. \n"
        )
        msg += str(e)
        raise msg

    install_args = ["install", to_install]

    if cloudsmith_url is not None:
        install_args.extend(["--index-url", cloudsmith_url])
    if not update_all:
        install_args.extend(["--no-deps"])
    if args:
        install_args.extend(args)
    try:
        resp += pip(*install_args)
        resp += pip("check")
    except:
        # try to install with constraints
        constraints_file_path = constraints_path or get_constraints_file_path(package_name)
        try:
            resp += install_with_constraints(
                to_install,
                constraints_file_path,
                cloudsmith_url,
                local,
                wheels_path,
                *args,
            )
        except:
            if slack_webhook_url is not None:
                send_upgrade_notification(
                    f"Failed to upgrade package {package_name}",
                    cloudsmith_url,
                    slack_webhook_url,
                )
            # if install with constraints fails or the installation caused broken dependencies
            # revert back to old package version
            if version is not None:
                package_name = package_name.split("==")[0]  # TODO: why ==?
                reinstall_args = [
                    "install",
                    "--no-deps",
                    f"{package_name}=={version}",
                ]
                if local:
                    reinstall_args.extend(["--find-links", wheels_path])
                else:
                    if cloudsmith_url:
                        reinstall_args.extend(["--index-url", cloudsmith_url])
                pip(*reinstall_args)
            else:
                raise
    return resp


def upgrade_from_local_wheel(
    package_install_cmd,
    skip_post_install,
    *args,
    cloudsmith_url=None,
    wheels_path=None,
    update_all=False,
    version=None,
    constraints_path=None,
):
    resp = ""
    package_name, _ = split_package_name_and_extra(package_install_cmd)
    try:
        resp = install_wheel(
            package_install_cmd,
            cloudsmith_url,
            local=True,
            wheels_path=wheels_path,
            update_all=update_all,
            version_cmd=version,
            constraints_path=constraints_path,
        )
    except Exception as e:
        response_err = str(e)
        return False, response_err
    if not skip_post_install:
        module_name = package_name.replace("-", "_").split("==")[0]
        try_running_module(module_name, *args)
    return "Successfully installed" in resp, resp


def attempt_to_install_version(
    package_install_cmd,
    version,
    cloudsmith_url=None,
    update_all=False,
    slack_webhook_url=None,
    constraints_path=None,
):
    """
    attempt to install a specific version of the given package
    """
    resp = ""
    pip_args = []
    if update_all:
        pip_args.append("--upgrade")
    args = tuple(arg for arg in pip_args)
    try:
        resp = install_wheel(
            package_install_cmd,
            cloudsmith_url,
            False,
            None,
            version,
            update_all,
            slack_webhook_url,
            constraints_path,
            *args,
        )
    except Exception as e:
        logging.info(f"Could not find {package_install_cmd} {version}")
        print(f"Could not find {package_install_cmd} {version}")
        return False, str(e)
    return "Successfully installed" in resp, resp


def attempt_upgrade(
    package_install_cmd,
    cloudsmith_url=None,
    update_all=False,
    slack_webhook_url=None,
    constraints_path=None,
    *args,
):
    """
    Attempt to upgrade a package with the given package_install_cmd.
    return True if it was upgraded.
    """
    pip_args = []
    match = is_development_cloudsmith(cloudsmith_url) or "--pre" in str(args)
    if match:
        pip_args.append("--pre")
    pip_args.append("--upgrade")
    args = tuple(arg for arg in pip_args)

    resp = install_wheel(
        package_install_cmd,
        cloudsmith_url,
        False,
        None,
        None,
        update_all,
        slack_webhook_url,
        constraints_path,
        *args,
    )
    was_upgraded = "Requirement already up-to-date" not in resp
    if was_upgraded:
        logging.info('"%s" package was upgraded.', package_install_cmd)
    else:
        logging.info('"%s" package was already up-to-date.', package_install_cmd)
    return was_upgraded, resp


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


def run_module_and_reload_uwsgi_app(module_name, *args):
    run_python_module(module_name, *args)
    package_name = module_name.replace("_", "-")
    reload_uwsgi_app(package_name)


def send_upgrade_notification(header, cloudsmith_url, slack_webhook_url):
    try:
        log_filepath = get_log_file_path().as_posix() or "log file"
        server_metadata = get_server_metadata()
        environment = "dev" if is_development_cloudsmith(cloudsmith_url) else "prod"
        text = f"{environment.upper()} - For more details, please audit {str(log_filepath)} at ({server_metadata})."
        send_slack_notification(
            header,
            text,
            slack_webhook_url,
        )
    except Exception as e:
        logging.error(f"Failed to send upgrade notification due to error: {e}")
        raise


def split_package_name_and_extra(package_install_cmd):
    extra_start = package_install_cmd.find("[")
    if extra_start != -1:
        package_name = package_install_cmd[:extra_start]
        extra = package_install_cmd[extra_start:]
    else:
        extra = ""
        package_name = package_install_cmd
    return package_name, extra


def try_running_module(wheel, cloudsmith_url=None, slack_webhook_url=None, *args):
    file_name = os.path.basename(wheel)
    module_name = file_name.split("-", 1)[0]
    # don't try running the module if it does not exists
    # prevents errors from being printed in case of trying
    # to run e.g. oll-core or oll-partners
    if util.find_spec(module_name) and util.find_spec(".__main__", package=module_name):
        try:
            run_module_and_reload_uwsgi_app(module_name, *args)
        except Exception:
            if slack_webhook_url is not None:
                send_upgrade_notification(
                    f"Failed to run module {module_name}",
                    cloudsmith_url,
                    slack_webhook_url,
                )
            raise
    else:
        logging.info("No module named %s", module_name)
        print(f"No module named {module_name}")


parser = argparse.ArgumentParser()
parser.add_argument(
    "--test",
    action="store_true",
    help="Determines whether log messages will be output to stdout, written to a log file and is used to determine logging level.",
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
    + "are expected to be in /vagrant/wheels directory",
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
parser.add_argument(
    "--format-output",
    action="store_true",
    help="Determines whether output of upgrade will be a JSON text response containing success and response",
)
parser.add_argument(
    "--update-all",
    action="store_true",
    help="Indicates that all packages should be updated",
)
parser.add_argument(
    "--slack-webhook-url",
    action="store",
    type=str,
    default=None,
    help="Slack webhook url string for sending slack notifications on failed upgrade",
)
parser.add_argument(
    "--constraints-path",
    action="store",
    help="Path to constraints.txt file"
)


def upgrade_python_package(
    package,
    wheels_path=None,
    version=None,
    cloudsmith_url=None,
    test=False,
    skip_post_install=False,
    should_run_initial_post_install=False,
    force=False,
    log_location=None,
    update_from_local_wheels=None,
    format_output=False,
    update_all=False,
    slack_webhook_url=None,
    constraints_path=None,
    *vars,
):
    success = False
    response_output = ""
    try:
        if test:
            logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
        else:
            log_location = log_location or "/var/log/upgrade_python_package.log"
            logging.basicConfig(
                filename=log_location,
                level=logging.WARNING,
                format="%(asctime)s %(message)s",
            )
        if cloudsmith_url:
            is_cloudsmith_url_valid(cloudsmith_url)
        wheels_path = wheels_path or "/vagrant/wheels"
        slack_webhook_url = slack_webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        if update_from_local_wheels:
            success, response_output = upgrade_from_local_wheel(
                package,
                skip_post_install,
                wheels_path=wheels_path,
                cloudsmith_url=cloudsmith_url,
                update_all=update_all,
                version=version,
                constraints_path=constraints_path,
                *vars,
            )
        elif should_run_initial_post_install:
            run_initial_post_install(package, *vars)
        else:
            success, response_output = upgrade_and_run(
                package,
                force,
                skip_post_install,
                version,
                cloudsmith_url,
                update_all,
                slack_webhook_url,
                constraints_path,
                *vars,
            )
    except Exception as e:
        if not format_output:
            raise e
        response_output += str(e)
    if format_output:
        while len(logging.root.handlers) > 0:
            logging.root.removeHandler(logging.root.handlers[-1])
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
        response = json.dumps({"success": success, "responseOutput": response_output})
        logging.info(response)
        print(response)


def main():
    parsed_args = parser.parse_args()
    test = parsed_args.test
    log_location = parsed_args.log_location
    wheels_path = parsed_args.wheels_path
    update_from_local_wheels = parsed_args.update_from_local_wheels
    package = parsed_args.package
    skip_post_install = parsed_args.skip_post_install
    cloudsmith_url = parsed_args.cloudsmith_url
    force = parsed_args.force
    should_run_initial_post_install = parsed_args.run_initial_post_install
    version = parsed_args.version
    format_output = parsed_args.format_output
    update_all = parsed_args.update_all
    slack_webhook_url = parsed_args.slack_webhook_url
    constraints_path = parsed_args.constraints_path
    upgrade_python_package(
        package,
        wheels_path,
        version,
        cloudsmith_url,
        test,
        skip_post_install,
        should_run_initial_post_install,
        force,
        log_location,
        update_from_local_wheels,
        format_output,
        update_all,
        slack_webhook_url,
        constraints_path,
        *parsed_args.vars,
    )


if __name__ == "__main__":

    main()
import argparse
import logging
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urljoin

import lxml.etree as et
import pip._vendor.requests as requests
from pip._vendor.packaging.utils import parse_wheel_filename

from upgrade.scripts.exceptions import RequiredArgumentMissing
from upgrade.scripts.upgrade_python_package import filter_versions, run
from upgrade.scripts.utils import (
    create_directory,
    on_rm_error,
    platform_specific_python_path,
)
from upgrade.scripts.validations import is_cloudsmith_url_valid

SYSTEM_DEPENDENCIES = ["pip", "setuptools", "upgrade-python-package"]
upgrade_success_re = re.compile(r'{"success": (true|false)')
response_output_re = re.compile(r'"responseOutput": "(.*?)"')


def venv_pip(venv_executable, *args, **kwargs):
    try:
        return run(*((venv_executable, "-m", "pip") + args), **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Error occurred while running pip in venv %s", str(e))
        raise e


def ensure_pip(venv_executable, *args, **kwargs):
    try:
        return run(*((venv_executable, "-m", "ensurepip") + args), **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Error occurred while running pip in venv %s", str(e))
        raise e


def venv(*args, **kwargs):
    try:
        return run(*((sys.executable, "-m", "venv", "--without-pip") + args), **kwargs)
    except subprocess.CalledProcessError as e:
        logging.error("Error occurred while creating venv %s", str(e))
        raise e


def upgrade_system_dependencies(venv_executable: str, dependencies: List[str]) -> None:
    for dependency in dependencies:
        try:
            # # FIXME: for local testing
            # if "upgrade-python-package" in dependency:
            #     venv_pip(
            #         venv_executable, "install", "-e", "D:\\OLL\\upgrade-python-package"
            #     )
            # else:
                venv_pip(venv_executable, "install", "--upgrade", f"{dependency}")
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error occurred while upgrading running pip upgrade {dependency} {str(e)}"
            )
            raise e


def upgrade_venv(
    venv_executable: str,
    requirements_obj: Any,
    cloudsmith_url: str,
    wheels_path: Optional[str],
    update_from_local_wheels: Optional[bool],
) -> str:
    try:
        log_path = Path("D:\\OLL\\upgrade-python-package\\venv.log")

        upgrade_args = [
            venv_executable,
            "-m",
            "upgrade.scripts.upgrade_python_package",
            requirements_obj.name,
            f"--cloudsmith-url={cloudsmith_url}",
            "--skip-post-install",
            f"--version={str(requirements_obj.specifier)}",
            f"--log-location={str(log_path)}",
            "--format-output",
        ]
        if wheels_path:
            upgrade_args.append(f"--wheels-path={wheels_path}")
        if update_from_local_wheels:
            upgrade_args.append("--update-from-local-wheels")

        return run(*(upgrade_args))
    except Exception as e:
        logging.error(
            f"Error occurred while upgrading {requirements_obj.name}{requirements_obj.specifier} {str(e)}"
        )
        raise e
    pass


def parse_requirements_txt(
    requirements_file: str,
) -> str:
    """Parse requirements.txt from repository.
    We expect following formats:
        ```
        dependency # oll.dependency.module.*
        ```
    or
        ```
        dependency~=2.6.7 # oll.dependency.module.*
        ```
    <Arguments>
        requirements_file: Path to requirements.txt file
    <Returns>
        str: Requirements
    """
    requirements_file = Path(requirements_file)

    if not Path(requirements_file).is_file():
        raise RequiredArgumentMissing(f"{requirements_file} does not exist")

    with open(requirements_file, "r") as requirements:
        for requirement in requirements.readlines():
            if "#" in requirement:
                requirements, _ = [s.strip() for s in requirement.split("#")]
                return requirements

    raise RequiredArgumentMissing(
        f"{requirements_file} does not contain a valid definition of a module"
    )


def _switch_venvs(venv_path: str) -> None:
    """
    Switch the virtualenv environments after a successful upgrade,
    since we first upgrade packages in a temporary `<venv_name>_backup` venv.
    """
    backup_venv_path = Path(str(venv_path) + "_backup")
    temp_venv_path = Path(str(venv_path) + "_temp")
    shutil.move(venv_path, temp_venv_path)
    shutil.move(backup_venv_path, venv_path)
    shutil.rmtree(temp_venv_path, onerror=on_rm_error)


def _get_venv_path(envs_home: str, requirements: str) -> Path:
    """Get the path to the virtualenv directory.
    Example:
    If requirements.txt contains:
        ```
        dependency==2.0.0 # oll.dependency.module.*
        ```
    Then the name of expected virtualenv directory is `<VENV_PATH> / dependency==2.0.0`
    """
    return Path(envs_home) / requirements


def create_venv(envs_home: str, requirements: str) -> str:
    """ """
    env_path = _get_venv_path(envs_home, requirements)
    create_directory(env_path)
    venv(*[str(env_path)])
    py_executable = platform_specific_python_path(str(env_path))
    ensure_pip(py_executable)
    upgrade_system_dependencies(py_executable, SYSTEM_DEPENDENCIES)

    return py_executable


def get_compatible_versions_from_package_index_html(
    requirements_obj: Any, package_index_html: str
) -> List[str]:
    """Parse the package index HTML list of available packages
    and return a list of package versions that are compatible"""
    tree = et.HTML(package_index_html)
    anchor_tags_el = tree.xpath("//a")
    parsed_packages_versions = [
        parse_wheel_filename(tag_el.text)[1] for tag_el in anchor_tags_el
    ]
    return filter_versions(requirements_obj.specifier, parsed_packages_versions)


def determine_compatible_upgrade_version(
    requirements_obj: Any, cloudsmith_url: str
) -> Optional[List[str]]:
    package_name = requirements_obj.name

    package_index_url = urljoin(cloudsmith_url, package_name)
    package_full_index_url = (
        package_index_url
        if package_index_url.endswith("/")
        else package_index_url + "/"
    )
    package_index_html = requests.get(package_full_index_url).text

    compatible_versions = get_compatible_versions_from_package_index_html(
        requirements_obj, package_index_html
    )
    if not compatible_versions or len(compatible_versions) == 1:
        """No compatible versions to upgrade"""
        return None

    return sorted(compatible_versions, reverse=True)[0]


def _venv_exists(envs_home: str, requirements: str) -> bool:
    return _get_venv_path(envs_home, requirements).exists()


def _get_venv_executable(venv_path: str) -> str:
    return platform_specific_python_path(venv_path)


def _to_requirements_obj(requirements: str) -> Any:
    try:
        """
        Note: a top-level `packaging` installation may be at a different version
        than the packaging version which pip vendors and uses internally.
        So, instead of using the top-level `packaging` module,
        we import the vendored version. This way we guarantee
        that the packaging APIs are matching pip's behavior exactly.
        """
        from pip._vendor.packaging.requirements import Requirement

        return Requirement(requirements)
    except Exception as e:
        logging.error(f"Error occurred while parsing requirements: {str(e)}")
        raise e


@contextmanager
def temporary_venv(venv_path: str) -> str:
    """Create a temporary virtualenv and return the path to the python executable."""
    try:
        backup_venv_path = Path(str(venv_path) + "_backup")
        shutil.copytree(venv_path, str(backup_venv_path))
        yield _get_venv_executable(backup_venv_path)
    except Exception as e:
        logging.error(f"Error occurred while creating temporary venv: {str(e)}")
        raise e
    finally:
        if backup_venv_path.exists():
            shutil.rmtree(backup_venv_path, onerror=on_rm_error)


def build_and_upgrade_venv(
    requirements: str,
    envs_home: str,
    auto_upgrade: bool,
    cloudsmith_url: str,
    wheels_path: Optional[str],
    update_from_local_wheels: Optional[bool],
) -> str:
    # two scenarios
    # requirements changed, so have to update
    # requirements did not change, have to determine if new version exists
    venv_path = str(_get_venv_path(envs_home, requirements))
    error_message = None
    if not _venv_exists(envs_home, requirements):
        auto_upgrade = True
        msg = "Requirements changed. Creating new virtualenv."
        print(msg)
        logging.info(msg)
        py_executable = create_venv(envs_home, requirements)
    else:
        py_executable = _get_venv_executable(venv_path)
        if not auto_upgrade:
            msg = "Requirements did not change. Returning venv executable."
            print(msg)
            logging.info(msg)
            return py_executable
    if auto_upgrade:
        requirements_obj = _to_requirements_obj(requirements)

        # this check needs to be a separate CLI command
        # TODO: what happens if the version is None but the package is not installed yet? e.g. ~=2.10.0
        version = determine_compatible_upgrade_version(requirements_obj, cloudsmith_url)

        if version is None:
            logging.info(
                f"Virtual environment {envs_home}/{requirements} is up to date. Skipping upgrade."
            )
            return py_executable

        with temporary_venv(venv_path) as temp_venv_executable:
            try:
                response = upgrade_venv(
                    temp_venv_executable,
                    requirements_obj,
                    cloudsmith_url,
                    wheels_path,
                    update_from_local_wheels,
                )
                logging.info(response)
            except Exception as e:
                logging.error(
                    f"Unexpected error occurred while upgrading {requirements_obj.name}{requirements_obj.specifier} {str(e)}"
                )
                raise e

            upgrade_successful = "true" in upgrade_success_re.search(response).group()
            if not upgrade_successful:
                response_error_msg = response_output_re.search(response).group(1)
                msg = f"Error occurred while upgrading {requirements_obj.name} to version {version}"
                logging.error(f"{msg} - {response_error_msg}")

            _switch_venvs(venv_path)

    return py_executable, error_message


def manage_venv(
    requirements_file=None,
    envs_home=None,
    auto_upgrade=False,
    cloudsmith_url=None,
    log_location=None,
    test=False,
    update_from_local_wheels=False,
    wheels_path=None,
):
    try:
        if test:
            logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
        else:
            log_location = log_location or "/var/log/manage_venv.log"
            logging.basicConfig(
                filename=log_location,
                level=logging.WARNING,
                format="%(asctime)s %(message)s",
            )
        if cloudsmith_url:
            is_cloudsmith_url_valid(cloudsmith_url)

        requirements = parse_requirements_txt(requirements_file)

        venv = build_and_upgrade_venv(
            requirements,
            envs_home,
            auto_upgrade,
            cloudsmith_url,
            wheels_path,
            update_from_local_wheels,
        )

    except Exception as e:
        logging.error(e)
        raise e


parser = argparse.ArgumentParser()

parser.add_argument(
    "--requirements-file",
    action="store",
    required=True,
    type=str,
    default=None,
    help="Path to the requirements.txt file within a repository."
    + "Requirements file is passed to pip install -r <requirements_file>.",
)
parser.add_argument(
    "--envs-home",
    action="store",
    type=str,
    required=True,
    default=None,
    help="Path to the home of all virtualenv directories",
)
parser.add_argument(
    "--auto-upgrade",
    action="store_true",
    help="Whether to automatically install/upgrade the package or "
    + "notify the user that a new version is available",
)
parser.add_argument("--no-auto-upgrade", dest="auto-upgrade", action="store_false")
parser.add_argument(
    "--cloudsmith-url",
    action="store",
    type=str,
    default=None,
    help="Cloudsmith URL with an API key necessary during local testing.",
)
parser.add_argument("--log-location", help="Specifies where to store the log file")
parser.add_argument(
    "--test",
    action="store_true",
    help="Determines whether log messages will be output to stdout "
    + "or written to a log file",
)
parser.add_argument(
    "--update-from-local-wheels",
    action="store_true",
    help="Determines whether to install packages from local wheels, which "
    + "are expected to be in /vagrant/wheels directory",
)
parser.add_argument(
    "--wheels-path",
    action="store",
    type=str,
    default=None,
    help="Path to the directory containing the wheels.",
)


def main():
    parsed_args = parser.parse_args()
    requirements_file = parsed_args.requirements_file
    envs_home = parsed_args.envs_home
    auto_upgrade = parsed_args.auto_upgrade
    cloudsmith_url = parsed_args.cloudsmith_url
    log_location = parsed_args.log_location
    test = parsed_args.test
    update_from_local_wheels = parsed_args.update_from_local_wheels
    wheels_path = parsed_args.wheels_path
    manage_venv(
        requirements_file=requirements_file,
        envs_home=envs_home,
        auto_upgrade=auto_upgrade,
        cloudsmith_url=cloudsmith_url,
        log_location=log_location,
        test=test,
        update_from_local_wheels=update_from_local_wheels,
        wheels_path=wheels_path,
    )


if __name__ == "__main__":
    main()

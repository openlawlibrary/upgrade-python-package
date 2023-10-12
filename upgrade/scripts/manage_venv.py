import argparse
import logging
import subprocess
import sys
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urljoin

import lxml.etree as et
import pip._vendor.requests as requests
from pip._vendor.packaging.utils import parse_wheel_filename

from upgrade.scripts.exceptions import RequiredArgumentMissing
from upgrade.scripts.upgrade_python_package import run
from upgrade.scripts.utils import create_directory, platform_specific_python_path
from upgrade.scripts.validations import is_cloudsmith_url_valid

SYSTEM_DEPENDENCIES = ["pip", "setuptools", "upgrade-python-package"]


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
    venv_executable: str, requirements_obj: Any, cloudsmith_url: str
) -> str:
    try:
        return run(
            *(
                (
                    venv_executable,
                    "-m",
                    "upgrade.scripts.upgrade_python_package",
                    requirements_obj.name,
                    f"--cloudsmith-url={cloudsmith_url}",
                    "--skip-post-install",
                    f"--version={str(requirements_obj.specifier)}",
                    "--test",
                    "--format-output",
                )
            )
        )
        breakpoint()
        print()
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


def venv_path(envs_home: str, requirements: str) -> Path:
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
    env_path = venv_path(envs_home, requirements)
    create_directory(env_path)
    venv(*[str(env_path)])
    py_executable = platform_specific_python_path(str(env_path))
    ensure_pip(py_executable)
    upgrade_system_dependencies(py_executable, SYSTEM_DEPENDENCIES)

    return py_executable


def _filter_versions(
    requirements_obj: Any, parsed_packages_versions: List[Any]
) -> List[str]:
    """Returns a list of versions that are compatible with the `SpecifierSet`.

    See https://packaging.pypa.io/en/latest/specifiers.html#specifiers for more details.

    Example:
        SpecifierSet("~=2.5.14").filter(["2.5.14", "2.5.15", "2.6.0", "3.0.0"])
        returns ["2.5.14", "2.5.15"]
    or:
        SpecifierSet("==2.5.14").filter(["2.5.14", "2.5.15", "2.6.0", "3.0.0"])
        returns ["2.5.14"]
    """
    return [
        str(version)
        for version in requirements_obj.specifier.filter(parsed_packages_versions)
    ]


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
    return _filter_versions(requirements_obj, parsed_packages_versions)


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
    return venv_path(envs_home, requirements).exists()


def _get_venv_executable(envs_home: str, requirements: str) -> str:
    return platform_specific_python_path(str(venv_path(envs_home, requirements)))


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
def temp_venv(venv_path: str) -> str:
    """Create a temporary virtualenv and return the path to the python executable."""
    try:
        backup_venv_path = Path(str(venv_path) + "_backup")
        shutil.copytree(venv_path, str(backup_venv_path))
        yield platform_specific_python_path(str(backup_venv_path))
    except Exception as e:
        logging.error(f"Error occurred while creating temporary venv: {str(e)}")
        raise e


def build_and_upgrade_venv(
    requirements: str,
    envs_home: str,
    auto_upgrade: bool,
    cloudsmith_url: str,
) -> str:
    # two scenarios
    # requirements changed, so have to update
    # requirements did not change, have to determine if new version exists

    if not _venv_exists(envs_home, requirements):
        # auto_upgrade = True # TODO: re-enable
        logging.info("Requirements changed. Creating new virtualenv.")
        py_executable = create_venv(envs_home, requirements)
    else:
        py_executable = _get_venv_executable(envs_home, requirements)

        if not auto_upgrade:
            logging.info(
                f"Requirements did not change. Returning {envs_home}/{requirements} venv."
            )
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

        with temp_venv(venv_path(envs_home, requirements)) as venv_executable:
            try:
                breakpoint()
                result = upgrade_venv(venv_executable, requirements_obj, cloudsmith_url)
                # entire result is printing to stdout
                print()
            except Exception as e:
                logging.error(
                    f"Unexpected error occurred while upgrading {requirements_obj.name}{requirements_obj.specifier} {str(e)}"
                )
                raise e
            

    return py_executable


def manage_venv(
    requirements_file=None,
    envs_home=None,
    auto_upgrade=False,
    cloudsmith_url=None,
    log_location=None,
    test=False,
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
            requirements, envs_home, auto_upgrade, cloudsmith_url
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


def main():
    parsed_args = parser.parse_args()
    requirements_file = parsed_args.requirements_file
    envs_home = parsed_args.envs_home
    auto_upgrade = parsed_args.auto_upgrade
    cloudsmith_url = parsed_args.cloudsmith_url
    log_location = parsed_args.log_location
    test = parsed_args.test
    manage_venv(
        requirements_file=requirements_file,
        envs_home=envs_home,
        auto_upgrade=auto_upgrade,
        cloudsmith_url=cloudsmith_url,
        log_location=log_location,
        test=test,
    )


if __name__ == "__main__":
    main()

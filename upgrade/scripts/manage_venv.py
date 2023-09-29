import argparse
import logging
from pathlib import Path

from upgrade.scripts.exceptions import RequiredArgumentMissing
from upgrade.scripts.validations import is_cloudsmith_url_valid


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
    action="store_false",
    help="Whether to automatically install/upgrade the package or "
    + "notify the user that a new version is available",
)
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

import argparse

def manage_venv(
    stele=None,
    envs_home=None,
    auto_upgrade=False,
    cloudsmith_url=None,
    log_location=None,
    test=False,
):
    pass

parser = argparse.ArgumentParser()

parser.add_argument(
    "--stele",
    action="store",
    required=True,
    type=str,
    default=None,
    help="Path to the stele repository containing requirements.txt file."
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
    stele = parsed_args.stele
    envs_home = parsed_args.envs_home
    auto_upgrade = parsed_args.auto_upgrade
    cloudsmith_url = parsed_args.cloudsmith_url
    log_location = parsed_args.log_location
    test = parsed_args.test
    manage_venv(
        stele=stele,
        envs_home=envs_home,
        auto_upgrade=auto_upgrade,
        cloudsmith_url=cloudsmith_url,
        log_location=log_location,
        test=test,
    )


if __name__ == "__main__":
    main()

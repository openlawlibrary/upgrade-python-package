import logging

from typing import Any, List
from pathlib import Path

from upgrade.scripts.exceptions import RequiredArgumentMissing

logger = logging.getLogger(__name__)


def filter_versions(
    specifier_set: Any, parsed_packages_versions: List[Any]
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
    return [str(version) for version in specifier_set.filter(parsed_packages_versions)]


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


def to_requirements_obj(requirements: str) -> Any:
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

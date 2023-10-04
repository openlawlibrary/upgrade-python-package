import pytest

from pathlib import Path
from functools import wraps

from upgrade.tests.utils import remove_directory

THIS_FOLDER = Path(__file__).parent
REPOSITORY_DIR = THIS_FOLDER.parent / "repository"


def env_fixture(make_dir=True):
    def decorator(func):
        @pytest.fixture(scope="module", autouse=True)
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                request = kwargs["request"]
                test_dir = Path(REPOSITORY_DIR, Path(request.node.name).stem)
                full_env_path = test_dir / "Environments"
                if full_env_path.is_dir():
                    remove_directory(str(full_env_path.parent))
                if make_dir:
                    full_env_path.mkdir(parents=True, exist_ok=True)
                yield from func(*args, **kwargs, path=str(full_env_path))
            except (Exception, KeyboardInterrupt) as e:
                raise e
            finally:
                remove_directory(str(full_env_path.parent))

        return wrapped

    return decorator


@env_fixture()
def envs_home(request, path=""):
    yield path


@pytest.fixture(scope="module")
def top_level_requirements(request, envs_home):
    test_package = Path(envs_home) / "test_repository"
    test_package.mkdir(parents=True, exist_ok=True)
    requirements_txt = test_package / "requirements.txt"
    requirements_txt.touch()

    with open(requirements_txt, "w") as requirements:
        requirements.write("oll-test-top-level~=2.0.0")

    yield (str(requirements_txt), "oll-test-top-level~=2.0.0")

import argparse
from contextlib import contextmanager
import subprocess
import os
import re
from pathlib import Path
import shutil


create_wheel_regex = re.compile(r"creating '(.+)\.whl")


@contextmanager
def chdir(dir):
    prev_cwd = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(prev_cwd)


def run(*command, **kwargs):
    """Run a command and return its output. Call with `debug=True` to print to
    stdout.
    In order to get bytes, call this command with `raw=True` argument.
    """
    # Skip decoding
    raw = kwargs.pop("raw", False)
    data = kwargs.pop("input", None)

    if len(command) == 1 and isinstance(command[0], str):
        command = command[0].split()

    def _format_word(word, **env):
        """To support words such as @{u} needed for git commands."""
        try:
            return word.format(env)
        except KeyError:
            return word

    command = [_format_word(word, **os.environ) for word in command]
    options = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    if not raw:
        options.update(universal_newlines=True)
    if data is not None:
        options.update(input=data)

    options.update(kwargs)
    completed = subprocess.run(command, **options)

    if completed.returncode != 0:
        return None

    return completed.stdout if raw else completed.stdout.rstrip()


parser = argparse.ArgumentParser()
parser.add_argument("--version", help="Version of test projects")
if __name__ == "__main__":
    parsed_args = parser.parse_args()
    version = parsed_args.version
    this_dir = Path(__file__).absolute().parent
    projects_dir = this_dir / "data"
    wheels_path = this_dir / "repository"
    wheels_path.mkdir(parents=True, exist_ok=True)
    for path in projects_dir.iterdir():
        if path == projects_dir:
            continue
        if version:
            version_path = path / "VERSION"
            if not version_path.is_file():
                version_path.touch()
            version_path.write_text(version)
        with chdir(str(path)):
            resp = run("python", "setup.py", "bdist_wheel")
            match = create_wheel_regex.findall(resp)
            if match is None:
                print(f"Failed to build {path}")
            else:
                wheel_path = path / f"{match[0]}.whl"
            shutil.copy(str(wheel_path), str(wheels_path))

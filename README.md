# upgrade-python-package
Small script for updating a python package (and its dependencies) and running post-install commands.

## Development

Install in editable mode with test dependencies:

```sh
uv pip install -e ".[test]"
```

Run tests:

```sh
pytest upgrade/tests
```

Note: the upgrade scripts prefer `uv pip` for install/uninstall operations when `uv` is available, and fall back to `python -m pip` otherwise.

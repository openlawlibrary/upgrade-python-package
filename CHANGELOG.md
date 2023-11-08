# Changelog

All _notable_ changes to this project will be documented in this file.

The format is based on _[Keep a Changelog][keepachangelog]_,
and this project adheres to a _modified_ form of _[Semantic Versioning][semver]_
(major version is the year; minor and patch are the same).

## [Unreleased]

### Added

- Added venv management script built on top of upgrade-python-package script ([#15])
- Added `find-compatible-versions` script which for a given venv, determines whether a new compatible update is available ([#15])

### Changed

- Drop Python 3.6, 3.7 support, add support for Python 3.11, 3.12 ([#15])

### Fixed

### Removed

[#15]: https://github.com/openlawlibrary/upgrade-python-package/pull/15

## [0.6.0]

### Added

- Integrate slack notifications ([#12])

### Changed

### Fixed

### Removed

[#12]: https://github.com/openlawlibrary/upgrade-python-package/pull/12

## [0.5.0]

### Added

- Add `update-all` flag to install packages without adding `--no-deps` ([#11])

### Changed

### Fixed

### Removed

[#11]: https://github.com/openlawlibrary/upgrade-python-package/pull/11

## [0.4.0]

### Added

### Changed

### Fixed

- Ignore pip version warnings, better error handling ([#10])

### Removed

[#10]: https://github.com/openlawlibrary/upgrade-python-package/pull/10

## [0.3.0]

### Added

### Changed

### Fixed

- Fix cloudsmith handling development repositories ([#9])

### Removed

[#9]: https://github.com/openlawlibrary/upgrade-python-package/pull/9

## [0.2.0]

### Added
- Fully support installation of local wheels ([#8])
- Add Python 3.10 support ([#8])

### Changed

### Fixed

### Removed

[#8]: https://github.com/openlawlibrary/upgrade-python-package/pull/8

## [0.1.0]

### Added

- Initial `upgrade-python-package` script ([#1])
- Initial testing framework ([#2]) ([#3])
- `data_files`` expected location changed to name of the package ([#5])
- Add script entry points ([#6])

### Changed

### Fixed

- Use `cloudsmith-url` ([#4])

### Removed

[#1]: https://github.com/openlawlibrary/upgrade-python-package/pull/1
[#2]: https://github.com/openlawlibrary/upgrade-python-package/pull/2
[#3]: https://github.com/openlawlibrary/upgrade-python-package/pull/3
[#4]: https://github.com/openlawlibrary/upgrade-python-package/pull/4
[#5]: https://github.com/openlawlibrary/upgrade-python-package/pull/5
[#6]: https://github.com/openlawlibrary/upgrade-python-package/pull/6

[Unreleased]:  https://github.com/openlawlibrary/upgrade-python-package/compare/0.6.0...HEAD
[0.6.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/0.5.0...0.6.0
[0.5.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/openlawlibrary/upgrade-python-package/compare/2f540d20eba15f0990770620c24904c613e1f1a8...0.1.0

[keepachangelog]: https://keepachangelog.com/en/1.0.0/
[semver]: https://semver.org/spec/v2.0.0.html
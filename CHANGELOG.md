# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project attempts to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.0.2 - 2020-03-22

### Added
 - New feature: list files in the format `package.name/relative/path.ext` in a
   new `package_data` target configuration key to find the file (relative to the
   named package) and copy it to the `<outdir>`.
 - New feature: include `add_setup_py=True` in any `[target:XXX]` section to
   produce a pip-installable Python package complete with an auto-generated
   `setup.py`.

### Fixed
 - Post-build commands now run in series (i.e., the second command won't be run
   until the first completes).

## 0.0.1 - 2020-02-26

First official release.

## Diffs
- [0.0.2](https://github.com/sclabs/treeshaker/compare/v0.0.1...v0.0.2)
- [0.0.1](https://github.com/sclabs/treeshaker/tree/v0.0.1)

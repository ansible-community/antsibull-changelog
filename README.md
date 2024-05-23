<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# antsibull-changelog -- Ansible Changelog Tool
[![Discuss on Matrix at #antsibull:ansible.com](https://img.shields.io/matrix/antsibull:ansible.com.svg?server_fqdn=ansible-accounts.ems.host&label=Discuss%20on%20Matrix%20at%20%23antsibull:ansible.com&logo=matrix)](https://matrix.to/#/#antsibull:ansible.com)
[![Nox badge](https://github.com/ansible-community/antsibull-changelog/workflows/nox/badge.svg?event=push&branch=main)](https://github.com/ansible-community/antsibull-changelog/actions?query=workflow%3A%22nox%22+branch%3Amain)
[![Codecov badge](https://img.shields.io/codecov/c/github/ansible-community/antsibull-changelog)](https://codecov.io/gh/ansible-community/antsibull-changelog)
[![REUSE status](https://api.reuse.software/badge/github.com/ansible-community/antsibull-changelog)](https://api.reuse.software/info/github.com/ansible-community/antsibull-changelog)

A changelog generator used by ansible-core and Ansible collections.

- Using the
  [`antsibull-changelog` CLI tool for collections](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelogs.md).
- Using the
  [`antsibull-changelog` CLI tool for other projects](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/other-projects.md).
- Documentation on the [`changelogs/config.yaml` configuration file for `antsibull-changelog`](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelog-configuration.md).
- Documentation on the
  [`changelog.yaml` format](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelog.yaml-format.md).

antsibull-changelog is covered by the [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

## Installation

It can be installed with pip:

    pip install antsibull-changelog

For python projects, `antsibull-changelog release` can retrieve the current
version from `pyproject.toml`.
You can install the project with

    pip install antsibull-changelog[toml]

to pull in the necessary toml parser for this feature.
The `toml` extra is always available, but it is noop on Python >= 3.11,
as `tomllib` is part of the standard library.

For more information, see the [documentation](https://ansible.readthedocs.io/projects/antsibull-changelog/).

## Development

Install and run `nox` to run all tests. That's it for simple contributions!
`nox` will create virtual environments in `.nox` inside the checked out project
and install the requirements needed to run the tests there.

To run specific tests:

1. `nox -e test` to only run unit tests;
2. `nox -e integration` to only run integration tests; this runs
   `antsibull-changelog lint` against antsibull-changelog and community.general
   (after cloning its repository) and records coverage data.
3. `nox -e coverage` to display combined coverage results after running `nox -e
   test integration`;
4. `nox -e lint` to run all linters and formatters at once;
5. `nox -e formatters` to run `isort` and `black`;
3. `nox -e codeqa` to run `flake8`, `pylint`, `reuse lint`, and `antsibull-changelog lint`;
7. `nox -e typing` to run `mypy` and `pyre`

## Creating a new release:

1. Run `nox -e bump -- <version> <release_summary_message>`. This:
   * Bumps the package version in `src/antsibull_changelog/__init__.py`.
   * Creates `changelogs/fragments/<version>.yml` with a `release_summary` section.
   * Runs `antsibull-changelog release` and adds the changed files to git.
   * Commits with message `Release <version>.` and runs `git tag -a -m 'antsibull-changelog <version>' <version>`.
   * Runs `hatch build --clean`.
2. Run `git push` to the appropriate remotes.
3. Once CI passes on GitHub, run `nox -e publish`. This:
   * Runs `hatch publish`;
   * Bumps the version to `<version>.post0`;
   * Adds the changed file to git and run `git commit -m 'Post-release version bump.'`;
4. Run `git push --follow-tags` to the appropriate remotes and create a GitHub release.

## License

Unless otherwise noted in the code, it is licensed under the terms of the GNU
General Public License v3 or, at your option, later. See
[LICENSES/GPL-3.0-or-later.txt](https://github.com/ansible-community/antsibull-changelog/tree/main/LICENSE)
for a copy of the license.

The repository follows the [REUSE Specification](https://reuse.software/spec/) for declaring copyright and
licensing information. The only exception are changelog fragments in ``changelog/fragments/``.

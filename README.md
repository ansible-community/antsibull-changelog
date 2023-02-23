<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# antsibull-changelog -- Ansible Changelog Tool
[![Discuss on Matrix at #community:ansible.com](https://img.shields.io/matrix/community:ansible.com.svg?server_fqdn=ansible-accounts.ems.host&label=Discuss%20on%20Matrix%20at%20%23community:ansible.com&logo=matrix)](https://matrix.to/#/#community:ansible.com)
[![Python linting badge](https://github.com/ansible-community/antsibull-changelog/workflows/Python%20linting/badge.svg?event=push&branch=main)](https://github.com/ansible-community/antsibull-changelog/actions?query=workflow%3A%22Python+linting%22+branch%3Amain)
[![Python testing badge](https://github.com/ansible-community/antsibull-changelog/workflows/Python%20testing/badge.svg?event=push&branch=main)](https://github.com/ansible-community/antsibull-changelog/actions?query=workflow%3A%22Python+testing%22+branch%3Amain)
[![Codecov badge](https://img.shields.io/codecov/c/github/ansible-community/antsibull-changelog)](https://codecov.io/gh/ansible-community/antsibull-changelog)

A changelog generator used by ansible-core and Ansible collections.

- Using the
  [`antsibull-changelog` CLI tool for collections](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelogs.rst).
- Using the
  [`antsibull-changelog` CLI tool for other projects](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/other-projects.rst).
- Documentation on the [`changelogs/config.yaml` configuration file for `antsibull-changelog`](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelog-configuration.rst).
- Documentation on the
  [`changelog.yaml` format](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelog.yaml-format.md).

antsibull-changelog is covered by the [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

## Installation

It can be installed with pip:

    pip install antsibull-changelog

For more information, see the
[documentation](https://github.com/ansible-community/antsibull-changelog/tree/main/docs/changelogs.rst).

## Using directly from git clone

Scripts are created by poetry at build time.  So if you want to run from
a checkout, you'll have to run them under poetry:

    python3 -m pip install poetry
    poetry install  # Installs dependencies into a virtualenv
    poetry run antsibull-changelog --help

If you want to create a new release:

    poetry build
    poetry publish  # Uploads to pypi.  Be sure you really want to do this

Note: When installing a package published by poetry, it is best to use pip >= 19.0.
Installing with pip-18.1 and below could create scripts which use pkg_resources
which can slow down startup time (in some environments by quite a large amount).

If you prefer to work with `pip install -e`, you can use [dephell](https://pypi.org/project/dephell/)
to create a `setup.py` file from `pyproject.toml`:

    dephell deps convert --from-path pyproject.toml --from-format poetry --to-path setup.py --to-format setuppy

Then you can install antsibull-changelog with `pip install -e .`.

## Build a release

First update the `version` entry in `pyproject.toml`. Then generate the changelog:

    antsibull-changelog release

Then build the build artefact:

    poetry build

Finally, publish to PyPi:

    poetry publish

Then tag the current state with the release version and push the tag to the repository.

## License

Unless otherwise noted in the code, it is licensed under the terms of the GNU
General Public License v3 or, at your option, later. See
[LICENSES/GPL-3.0-or-later.txt](https://github.com/ansible-community/antsibull-changelog/tree/main/LICENSE)
for a copy of the license.

The repository follows the [REUSE Specification](https://reuse.software/spec/) for declaring copyright and
licensing information. The only exception are changelog fragments in ``changelog/fragments/``.

<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# antsibull-changelog

[![Discuss on Matrix at #antsibull:ansible.com](https://img.shields.io/matrix/antsibull:ansible.com.svg?server_fqdn=ansible-accounts.ems.host&label=Discuss%20on%20Matrix%20at%20%23antsibull:ansible.com&logo=matrix)](https://matrix.to/#/#antsibull:ansible.com)
[![Nox badge](https://github.com/ansible-community/antsibull-changelog/workflows/nox/badge.svg?event=push&branch=main)](https://github.com/ansible-community/antsibull-changelog/actions?query=workflow%3A%22nox%22+branch%3Amain)
[![Codecov badge](https://img.shields.io/codecov/c/github/ansible-community/antsibull-changelog)](https://codecov.io/gh/ansible-community/antsibull-changelog)

A changelog generator used by ansible-core and Ansible collections.

- Using the [`antsibull-changelog` CLI tool for collections](changelogs.md).
- Using the [`antsibull-changelog` CLI tool for other projects](other-projects.md).
- Documentation on the [`changelogs/config.yaml` configuration file for `antsibull-changelog`](changelog-configuration.md).
- Documentation on the [`changelog.yaml` format](changelog.yaml-format.md).

antsibull-changelog is covered by the [Ansible Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).

To see how antsibull-changelog changes, please look at the
[antsibull-changelog changelog](https://github.com/ansible-community/antsibull-changelog/blob/main/CHANGELOG.md).

> Need help or want to discuss the project? See our [Community guide](community.md) to learn how to join the conversation!

## Installation

It can be installed with pip:

```console
pip install antsibull-changelog
```

For python projects, `antsibull-changelog release` can retrieve the current
version from `pyproject.toml`.
You can install the project with

```console
pip install antsibull-changelog[toml]
```

to pull in the necessary toml parser for this feature.
The `toml` extra is always available, but it is noop on Python >= 3.11,
as `tomllib` is part of the standard library.

For more information, see the [documentation](changelogs.md).

## License

Unless otherwise noted in the code, it is licensed under the terms of the GNU
General Public License v3 or, at your option, later. See
[LICENSES/GPL-3.0-or-later.txt](https://github.com/ansible-community/antsibull-changelog/tree/main/LICENSE)
for a copy of the license.

The repository follows the [REUSE Specification](https://reuse.software/spec/) for declaring copyright and
licensing information. The only exception are changelog fragments in ``changelog/fragments/``.

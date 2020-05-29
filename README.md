# antsibull-changelog -- Ansible Changelog Tool

A changelog generator used by Ansible and Ansible collections.

- Using the [`antsibull-changelog` CLI tool](docs/changelogs.rst).
- Documentation on the [`changelog.yaml` format](docs/changelog.yaml-format.md).

Scripts are created by poetry at build time.  So if you want to run from
a checkout, you'll have to run them under poetry::

    python3 -m pip install poetry
    poetry install  # Installs dependencies into a virtualenv
    poetry run antsibull-changelog --help

If you want to create a new release::

    poetry build
    poetry publish  # Uploads to pypi.  Be sure you really want to do this

.. note:: When installing a package published by poetry, it is best to use
    pip >= 19.0.  Installing with pip-18.1 and below could create scripts which
    use pkg_resources which can slow down startup time (in some environments by
    quite a large amount).

Unless otherwise noted in the code, it is licensed under the terms of the GNU
General Public License v3 or, at your option, later.

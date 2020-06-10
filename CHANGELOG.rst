====================================
Changelog for Ansible Changelog Tool
====================================


v0.3.0
======

Minor Changes
-------------

- Changelog generator can be ran via ``python -m antsibull_changelog``.

v0.2.1
======

Bugfixes
--------

- Allow to enumerate plugins/modules with ansible-doc by specifying ``--use-ansible-doc``.

v0.2.0
======

Minor Changes
-------------

- Title generation improved (remove superfluous space).
- ``lint`` subcommand no longer requires specification whether it is run inside a collection or not (if usual indicators are absent).
- Improve reStructuredText creation when new modules with and without namespace exist at the same time.
- Improve error handling.
- Fix internal API for ACD changelog generation (pruning and concatenation of changelogs).
- Use PyYAML C loader/dumper if available.
- Added more testing.

v0.1.0
======

Initial release as antsibull-changelog. The Ansible Changelog Tool has originally been developed by @mattclay in `the ansible/ansible <https://github.com/ansible/ansible/blob/stable-2.9/packaging/release/changelogs/changelog.py>`_ repository for Ansible itself. It has been extended in `felixfontein/ansible-changelog <https://github.com/felixfontein/ansible-changelog/>`_ and `ansible-community/antsibull <https://github.com/ansible-community/antsibull/>`_ to work with collections, until it was moved to its current location `ansible-community/antsibull-changelog <https://github.com/ansible-community/antsibull-changelog/>`_.

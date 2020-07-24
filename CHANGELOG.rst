====================================
Changelog for Ansible Changelog Tool
====================================

.. contents::
   :local:
   :depth: 1

v0.7.0
======

Minor Changes
-------------

- A new config option, ``ignore_other_fragment_extensions`` allows for configuring whether only ``.yaml`` and ``.yml`` files are used (as mandated by the ``ansible-test sanity --test changelog`` test). The default value for existing configurations is ``false``, and for new configurations ``true``.

v0.6.0
======

Minor Changes
-------------

- The config option ``archive_path_template`` allows to move fragments into an archive directory when ``keep_fragments`` is set to ``false``.
- New changelog configurations place the ``CHANGELOG.rst`` file by default in the top-level directory, and not in ``changelogs/``.
- The option ``use_fqcn`` (set to ``true`` in new configurations) allows to use FQCN for new plugins and modules.

v0.5.0
======

Minor Changes
-------------

- The internal changelog generator code got more flexible to help antsibull generate Ansible porting guides.

v0.4.0
======

Minor Changes
-------------

- Allow to enable or disable flatmapping via ``config.yaml``.

Bugfixes
--------

- Fix bad module namespace detection when collection was symlinked into Ansible's collection search path. This also allows to add releases to collections which are not installed in a way that Ansible finds them.

v0.3.1
======

Bugfixes
--------

- Improve error message when ``--is-collection`` is specified and ``changelogs/config.yaml`` cannot be found, or when the ``lint`` subcommand is used.
- Improve behavior when ``changelogs/config.yaml`` is not a dictionary, or does not contain ``sections``.
- Do not fail when ``changelogs/fragments`` does not exist. Simply assume there are no fragments in that case.

v0.3.0
======

Minor Changes
-------------

- Changelog generator can be ran via ``python -m antsibull_changelog``.
- Allow to pass path to ansible-doc binary via ``--ansible-doc-bin``.
- Use ``ansible-doc`` instead of ``/path/to/checkout/bin/ansible-doc`` when being run in ansible-base checkouts.

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

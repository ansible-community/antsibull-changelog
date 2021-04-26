====================================
Changelog for Ansible Changelog Tool
====================================

.. contents::
   :local:
   :depth: 1

v0.10.0
=======

Minor Changes
-------------

- The new ``--cummulative-release`` option for ``antsibull-changelog release`` allows to add all plugins and objects to a release since whose ``version_added`` is later than the previous release version (or ancestor if there was no previous release), and at latest the current release version. This is needed for major releases of ``community.general`` and similarly organized collections.
- Will now print a warning when a release is made where the no ``prelude_section_name`` section (default: ``release_summary``) appears.

Bugfixes
--------

- Make sure that the plugin caching inside ansible-base/-core works without ``--use-ansible-doc``.

v0.9.0
======

Breaking Changes
----------------

- The new option ``prevent_known_fragments`` with default value being the value of ``keep_fragments`` allows to control whether fragments with names that already appeared in the past are ignored or not. The new behavior happens if ``keep_fragments=false``, and is less surprising to users (see https://github.com/ansible-community/antsibull-changelog/issues/46). Changelogs with ``keep_fragments=true``, like the ansible-base/ansible-core changelog, are not affected.

Major Changes
-------------

- Add support for reporting new playbooks and roles in collections.
- Add support for special changelog fragment sections which add new plugins and/or objects to the changelog for this version. This is mainly useful for ``test`` and ``filter`` plugins, and for ``playbook`` and ``role`` objects, which are not yet automatically detected and mentioned in ``changelogs/changelog.yaml`` or the generated RST changelog.

  The format of these sections and their content is as follows::

      ---
      add plugin.filter:
        - name: to_time_unit
          description: Converts a time expression to a given unit
        - name: to_seconds
          description: Converts a time expression to seconds
      add object.role:
        - name: nginx
          description: The most awesome nginx installation role ever
      add object.playbook:
        - name: wipe_server
          description: Totally wipes a server

  For every entry, a list of plugins (section ``add plugin.xxx``) or objects (section ``add object.xxx``) of the given type (``filter``, ``test`` for plugins, ``playbook``, ``role`` for objects) will be added. Every plugin or object has a short name as well as a short description. These fields correspond to the module/plugin name and the ``short_description`` field of the ``DOCUMENTATION`` block of modules and documentable plugins.

Minor Changes
-------------

- Add ``--update-existing`` option for ``antsibull-changelog release``, which allows to update the current release's release date and (if relevant) codename instead of simply reporting that the release already exists.

v0.8.1
======

Bugfixes
--------

- Fixed error on generating changelogs when using the trivial section.

v0.8.0
======

Minor Changes
-------------

- Allow to sanitize changelog data on load/save. This means that unknown information will be removed, and bad information will be stripped. This will be enabled in newly created changelog configs, but is disabled for backwards compatibility.
- Allow to not save a changelog on release when using API.

v0.7.0
======

Minor Changes
-------------

- A new config option, ``ignore_other_fragment_extensions`` allows for configuring whether only ``.yaml`` and ``.yml`` files are used (as mandated by the ``ansible-test sanity --test changelog`` test). The default value for existing configurations is ``false``, and for new configurations ``true``.
- Refactoring changelog generation code to provide all preludes (release summaries) in changelog entries, and provide generic functionality to extract a grouped list of versions. These changes are mainly for the antsibull project.
- Allow to use semantic versioning also for Ansible-base with the ``use_semantic_versioning`` configuration setting.

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

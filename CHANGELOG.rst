====================================
Ansible Changelog Tool Release Notes
====================================

.. contents:: Topics

v0.26.0
=======

Release Summary
---------------

Feature release.

Minor Changes
-------------

- The Markdown output format is now compatible with `python-markdown <https://python-markdown.github.io/>`_ and `mkdocs <https://www.mkdocs.org/>`_, as long as the `pymdownx.escapeall <https://facelessuser.github.io/pymdown-extensions/extensions/escapeall/>`_ extension is enabled (https://github.com/ansible-community/antsibull-changelog/pull/153).

v0.25.0
=======

Release Summary
---------------

Bugfix and feature release.

Minor Changes
-------------

- Add ``--version`` flag to print package version and exit (https://github.com/ansible-community/antsibull-changelog/pull/147).

Bugfixes
--------

- When multiple output formats are defined and ``antsibull-changelog generate`` is used with both ``--output`` and ``--output-format``, an error was displayed that ``--output-format`` must be specified (https://github.com/ansible-community/antsibull-changelog/issues/149, https://github.com/ansible-community/antsibull-changelog/pull/151).

v0.24.0
=======

Release Summary
---------------

Feature release which now allows to output MarkDown.

Minor Changes
-------------

- Allow automatically retrieving package version for hatch projects with the ``hatch version`` command (https://github.com/ansible-community/antsibull-changelog/pull/141).
- Allow to render changelogs as MarkDown. The output formats written can be controlled with the ``output_formats`` option in the config file (https://github.com/ansible-community/antsibull-changelog/pull/139).
- Officially support Python 3.12 (https://github.com/ansible-community/antsibull-changelog/pull/134).

Deprecated Features
-------------------

- Some code in ``antsibull_changelog.changelog_entry`` has been deprecated, and the ``antsibull_changelog.rst`` module has been deprecated completely. If you use them in your own code, please take a look at the `PR deprecating them <https://github.com/ansible-community/antsibull-changelog/pull/139>`__ for information on how to stop using them (https://github.com/ansible-community/antsibull-changelog/pull/139).

v0.23.0
=======

Release Summary
---------------

Feature release.

Minor Changes
-------------

- Allow to generate changelog for a specific version (https://github.com/ansible-community/antsibull-changelog/pull/130).
- Allow to generate only the last entry without preamble with the ``generate`` command (https://github.com/ansible-community/antsibull-changelog/pull/131).
- Allow to write ``generate`` output to a user-provided file (https://github.com/ansible-community/antsibull-changelog/pull/131).

v0.22.0
=======

Release Summary
---------------

New feature release

Minor Changes
-------------

- Add ``antsibull-changelog-lint`` and ``antsibull-changelog-lint-changelog-yaml`` pre-commit.com hooks (https://github.com/ansible-community/antsibull-changelog/pull/125).
- Add ``toml`` extra to pull in a toml parser to use to guess the version based on ``pyproject.toml`` (https://github.com/ansible-community/antsibull-changelog/pull/126).

v0.21.0
=======

Release Summary
---------------

Maintenance release with a deprecation.

Deprecated Features
-------------------

- Support for ``classic`` changelogs is deprecated and will be removed soon. If you need to build changelogs for Ansible 2.9 or before, please use an older version (https://github.com/ansible-community/antsibull-changelog/pull/123).

v0.20.0
=======

Release Summary
---------------

Bugfix and maintenance release using a new build system.

Major Changes
-------------

- Change pyproject build backend from ``poetry-core`` to ``hatchling``. ``pip install antsibull`` works exactly the same as before, but some users may be affected depending on how they build/install the project (https://github.com/ansible-community/antsibull-changelog/pull/109).

Bugfixes
--------

- When releasing ansible-core and only one of ``--version`` and ``--codename`` is supplied, error out instead of ignoring the supplied value (https://github.com/ansible-community/antsibull-changelog/issues/104, https://github.com/ansible-community/antsibull-changelog/pull/105).

v0.19.0
=======

Release Summary
---------------

Feature release.

Minor Changes
-------------

- Allow to extract other project versions for JavaScript / TypeScript projects from ``package.json`` (https://github.com/ansible-community/antsibull-changelog/pull/100).
- Allow to extract other project versions for Python projects from PEP 621 conformant ``pyproject.toml`` (https://github.com/ansible-community/antsibull-changelog/pull/100).
- Support Python 3.11's ``tomllib`` to load ``pyproject.toml`` (https://github.com/ansible-community/antsibull-changelog/issues/101, https://github.com/ansible-community/antsibull-changelog/pull/102).
- Use more specific exceptions than ``Exception`` for some cases in internal code (https://github.com/ansible-community/antsibull-changelog/pull/103).

v0.18.0
=======

Release Summary
---------------

Maintenance release that drops support for older Python versions.

Breaking Changes / Porting Guide
--------------------------------

- Drop support for Python 3.6, 3.7, and 3.8 (https://github.com/ansible-community/antsibull-changelog/pull/93).

v0.17.0
=======

Release Summary
---------------

Feature release for ansible-core.

Minor Changes
-------------

- Only allow a ``trival`` section in the ansible-core/ansible-base changelog when explicitly configured (https://github.com/ansible-community/antsibull-changelog/pull/90).

v0.16.0
=======

Release Summary
---------------

Feature and bugfix release.

Minor Changes
-------------

- Allow to extract other project versions for Python poetry projects from ``pyproject.toml`` (https://github.com/ansible-community/antsibull-changelog/pull/80).
- The files in the source repository now follow the `REUSE Specification <https://reuse.software/spec/>`_. The only exceptions are changelog fragments in ``changelogs/fragments/`` (https://github.com/ansible-community/antsibull-changelog/pull/82).

Bugfixes
--------

- Mark rstcheck 4.x and 5.x as compatible. Support rstcheck 6.x as well (https://github.com/ansible-community/antsibull-changelog/pull/81).

v0.15.0
=======

Release Summary
---------------

Feature release.

Minor Changes
-------------

- Add ``changelogs/changelog.yaml`` file format linting subcommand that was previously part of antsibull-lint (https://github.com/ansible-community/antsibull-changelog/pull/76, https://github.com/ansible-community/antsibull/issues/410).

v0.14.0
=======

Release Summary
---------------

Feature release that will speed up the release process with ansible-core 2.13.

Minor Changes
-------------

- The internal ``changelog.yaml`` linting API allows to use ``packaging.version.Version`` for version numbers instead of semantic versioning (https://github.com/ansible-community/antsibull-changelog/pull/73).
- Use the new ``--metadata-dump`` option for ansible-core 2.13+ to quickly dump and extract all module/plugin ``version_added`` values for the collection (https://github.com/ansible-community/antsibull-changelog/pull/72).

v0.13.0
=======

Release Summary
---------------

This release makes changelog building more reliable.

Minor Changes
-------------

- Always lint fragments before releasing (https://github.com/ansible-community/antsibull-changelog/issues/65, https://github.com/ansible-community/antsibull-changelog/pull/67).

Bugfixes
--------

- Fix issues with module namespaces when symlinks appear in the path to the temp directory (https://github.com/ansible-community/antsibull-changelog/issues/68, https://github.com/ansible-community/antsibull-changelog/pull/69).
- Stop mentioning ``galaxy.yaml`` instead of ``galaxy.yml`` in some error messages (https://github.com/ansible-community/antsibull-changelog/pull/66).

v0.12.0
=======

Release Summary
---------------

New feature release which supports other projects than ansible-core and Ansible collections.

Minor Changes
-------------

- Support changelogs for other projects than ansible-core/-base and Ansible collections (https://github.com/ansible-community/antsibull-changelog/pull/60).

Bugfixes
--------

- Fix prerelease collapsing when ``use_semantic_versioning`` is set to ``true`` for ansible-core.

v0.11.0
=======

Minor Changes
-------------

- When using ansible-core 2.11 or newer, will now detect new roles with argument spec. We only consider the ``main`` entrypoint of roles.

Bugfixes
--------

- When subdirectories of ``modules`` are used in ansible-base/ansible-core, the wrong module name was passed to ``ansible-doc`` when ``--use-ansible-doc`` was not used.

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

Breaking Changes / Porting Guide
--------------------------------

- The new option ``prevent_known_fragments`` with default value being the value of ``keep_fragments`` allows to control whether fragments with names that already appeared in the past are ignored or not. The new behavior happens if ``keep_fragments=false``, and is less surprising to users (see https://github.com/ansible-community/antsibull-changelog/issues/46). Changelogs with ``keep_fragments=true``, like the ansible-base/ansible-core changelog, are not affected.

v0.8.1
======

Bugfixes
--------

- Fixed error on generating changelogs when using the trivial section.

v0.8.0
======

Minor Changes
-------------

- Allow to not save a changelog on release when using API.
- Allow to sanitize changelog data on load/save. This means that unknown information will be removed, and bad information will be stripped. This will be enabled in newly created changelog configs, but is disabled for backwards compatibility.

v0.7.0
======

Minor Changes
-------------

- A new config option, ``ignore_other_fragment_extensions`` allows for configuring whether only ``.yaml`` and ``.yml`` files are used (as mandated by the ``ansible-test sanity --test changelog`` test). The default value for existing configurations is ``false``, and for new configurations ``true``.
- Allow to use semantic versioning also for Ansible-base with the ``use_semantic_versioning`` configuration setting.
- Refactoring changelog generation code to provide all preludes (release summaries) in changelog entries, and provide generic functionality to extract a grouped list of versions. These changes are mainly for the antsibull project.

v0.6.0
======

Minor Changes
-------------

- New changelog configurations place the ``CHANGELOG.rst`` file by default in the top-level directory, and not in ``changelogs/``.
- The config option ``archive_path_template`` allows to move fragments into an archive directory when ``keep_fragments`` is set to ``false``.
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

- Do not fail when ``changelogs/fragments`` does not exist. Simply assume there are no fragments in that case.
- Improve behavior when ``changelogs/config.yaml`` is not a dictionary, or does not contain ``sections``.
- Improve error message when ``--is-collection`` is specified and ``changelogs/config.yaml`` cannot be found, or when the ``lint`` subcommand is used.

v0.3.0
======

Minor Changes
-------------

- Allow to pass path to ansible-doc binary via ``--ansible-doc-bin``.
- Changelog generator can be ran via ``python -m antsibull_changelog``.
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

- Added more testing.
- Fix internal API for ACD changelog generation (pruning and concatenation of changelogs).
- Improve error handling.
- Improve reStructuredText creation when new modules with and without namespace exist at the same time.
- Title generation improved (remove superfluous space).
- Use PyYAML C loader/dumper if available.
- ``lint`` subcommand no longer requires specification whether it is run inside a collection or not (if usual indicators are absent).

v0.1.0
======

Release Summary
---------------

Initial release as antsibull-changelog. The Ansible Changelog Tool has originally been developed by @mattclay in `the ansible/ansible <https://github.com/ansible/ansible/blob/stable-2.9/packaging/release/changelogs/changelog.py>`_ repository for Ansible itself. It has been extended in `felixfontein/ansible-changelog <https://github.com/felixfontein/ansible-changelog/>`_ and `ansible-community/antsibull <https://github.com/ansible-community/antsibull/>`_ to work with collections, until it was moved to its current location `ansible-community/antsibull-changelog <https://github.com/ansible-community/antsibull-changelog/>`_.

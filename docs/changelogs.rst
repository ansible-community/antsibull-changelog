**************************
Changelogs for Collections
**************************

The ``antsibull-changelog`` tool allows you to create and update changelogs for Ansible collections, that are similar to the ones provided by Ansible itself in earlier versions, and that are compatible to the combined Ansible Community Distribution changelogs.

The following instructions assume that antsibull has been properly installed, for example via ``pip install antsibull-changelog``. This is the preferred way to install ``antsibull-changelog``.

If you want to get the current ``main`` branch with not yet released changes, run ``pip install https://github.com/ansible-community/antsibull-changelog/archive/main.tar.gz``. If you cloned the git repository and want to run it from there with ``poetry``, ``antsibull-changelog`` has to be substituted with ``poetry run antsibull-changelog``.

Bootstrapping changelogs for collections
========================================

To set up ``antsibull-changelog``, run::

    antsibull-changelog init /path/to/your/collection

This is the directory which contains ``galaxy.yml``. This creates subdirectories ``changelogs/`` and ``changelogs/fragments/``, and a configuration file ``changelogs/config.yaml``. Adjust the configuration file to your needs. The settings of highest interest are:

#. ``title``: This is by default the titlecase of your collection's namespace and name. Feel free to insert a nicer name here.
#. ``keep_fragments``: The default value ``false`` removes the fragment files after a release is done. If you prefer to keep fragment files for older releases, set this to ``true``. If you want to remove fragments after a release, but archive them in another directory, you can use the ``archive_path_template`` option in combination with ``keep_fragments: no`. See further below in the list for its usage.
#. ``changelog_filename_template``: The default value ``../CHANGELOG.rst`` is relative to the ``changelogs/`` directory.
#. ``use_fqcn``: The default value ``true`` uses FQCN when mentioning new plugins and modules.
#. ``flatmap``: Setting to ``true`` or ``false`` explicitly enables resp. disables flatmapping. Since flatmapping is disabled by default (except for ansible-base), this is effectively only needed for the big community collections ``community.general`` and ``community.network``.
#. ``always_refresh``: See :ref:`refreshing` on refreshing changelog fragments and/or plugin descriptions.
#. ``archive_path_template``: If ``keep_fragments`` is set to ``false``, and ``archive_path_template`` is set, fragments will be copied into the directory denoted by ``archive_path_template`` instead of being deleted. The directory is created if it does not exist. The placeholder ``{version}`` can be used for the current collection version into which the fragment was included.
#. ``ignore_other_fragment_extensions``: If set to ``true``, only ``.yml`` and ``.yaml`` fragment filenames are considered which do not start with a dot. This is compatible with what ``ansible-test sanity --test changelog`` enforces. If set to ``false`` (default if not specified), all filenames that do not start with a dot are accepted.

A description of all configuration settings, see the separate document `Configuration Settings for Changelogs for Collections <./changelog-configuration.rst>`_.

Validating changelog fragments
==============================

If you want to do a basic syntax check of changelog fragments, you can run::

    antsibull-changelog lint

If you want to check a specific fragment, you can provide a path to it; otherwise, all fragments in ``changelogs/fragments/`` are checked. This can be used in CI to avoid contributors to check in invalid changelog fragments, or introduce new sections (by mistyping existing ones, or simply guessing wrong names).

If ``antsibull-changelog lint`` produces no output on stdout, and exits with exit code 0, the changelog fragments are OK. If errors are found, they are reported by one line in stdout for each error in the format ``path/to/fragment:line:column:message``, and the program exits with exit code 3. Other exit codes indicate problems with the command line or during the execution of the linter.

Releasing a new version of a collection
=======================================

To release a new version of a collection, you need to run::

    antsibull-changelog release

inside your collection's tree. This assumes that ``galaxy.yml`` exists and its version is the version of the release you want to make. If that file does not exist, or has a wrong value for ``version``, you can explicitly specify the version you want to release::

    antsibull-changelog release --version 1.0.0

You can also specify a release date with ``--date 2020-12-31``, if the default (today) is not what you want.

When doing a release, the changelog generator will read all changelog fragments which are not already mentioned in the changelog, and include them in a new entry in ``changelogs/changelog.yaml``. It will also scan metadata for all modules and plugins of your collection, and mention all modules and plugins with ``version_added`` equal to this version as new modules/plugins.

The metadata for modules and plugins is stored in ``changelogs/.plugin-cache.yaml``, and is only recalculated once the release version changes. To force recollecting this data, either delete the file, or specify the ``--reload-plugins`` option to ``antsibull-changelog release``.

After running ``antsibull-changelog release``, you should check ``changelogs/changelog.yaml`` and the generated reStructuredText file (by default ``CHANGELOG.rst``) in.

.. _refreshing:

Updating/Refreshing changelog.yaml
==================================

By default, the ``changelogs/changelog.yaml`` file is the main source of truth for antsibull-changelog. It is only modified when a new release is done, and in that case existing entries for other versions than the current one are not touched.

If the main source of truth should be the fragments, or the plugin sources, the refreshing options or config has to be used.

Please note that for plugins, a cache is created in ``changelogs/.plugin-cache.yaml``. This cache is updated when the ``generate`` and ``release`` subcommands are run, and the latest version (for ``generate``) resp. the release version (for ``release``) differs from the version recorded in the cache file. Regeneration can be enforced by specifying the ``--reload-plugins`` option.

This means that if plugin descriptions should be updated, either the plugin cache has to be deleted, or ``--reload-plugins`` has to be specified next to the refresh options/configuration. Refreshing can be configured in different ways, either by the ``always_refresh`` configuration setting, or three command line options ``--refresh``, ``--refresh-plugins`` and ``--refresh-fragments``. These can be specified for both the ``generate`` and ``release`` subcommands.

#. The ``always_refresh`` configuration is a string with one of the following values:
    * ``none`` (default): equivalent to ``--refresh-plugins``, ``--refresh-fragments``, and ``--refresh`` not specified;
    * ``full``: equivalent to ``--refresh-plugins allow-removal --refresh-fragments with-archives`` specified, or alternatively ``--refresh``;
    * a comma-separated list, where the following entries are supported:
        * ``plugins``: equivalent to ``--refresh-plugins allow-removal`` specified;
        * ``plugins-without-removal``: equivalent to ``--refresh-plugins prevent-removal`` specified;
        * ``fragments``: equivalent to ``--refresh-fragments with-archives`` specified;
        * ``fragments-without-archives``: equivalent to ``--refresh-fragments without-archives`` specified.

#. The ``--refresh`` command line parameter is equivalent to ``--refresh-plugins allow-removal --refresh-fragments with-archives``.

#. ``--refresh-plugins``: if specified, plugin and module descriptions are updated from the plugin cache.
    * ``allow-removal`` (default): Plugin and module descriptions are updated. If a module or plugin does not exist in the cache, it will be **removed** from the changelog. Please note that if you do not start a new changelog per major release of a collection, and have removed plugins or modules before, ``--refresh plugins allow-removal`` will remove earlier changelog entries from when these plugins resp. modules were added!
    * ``prevent-removal``: Plugin and module descriptions are updated. If a module or plugin does not exist in the cache, it will **not** be removed from the changelog.

#. ``--refresh-fragments``: if specified, the fragments for all versions will be recreated from the changelog fragment files. This is only possible if ``keep_fragments`` is ``true``, or fragment archives exist (see the ``archive_path_template`` option). Note that if not all fragments were archived or kept in the fragments directory, they will be **removed** from the changelog.
    * ``with-archives`` (default): Uses both the archives and the current fragment directory to update the fragments.
    * ``without-archives``: Uses only the current fragment directory to update the fragments. Fragments that have been moved to the archive and no longer exist in the fragment directory will vanish from the changelog.

Changelog Fragment Categories
=============================

This section describes the section categories created in the default config. You can change them, though this is strongly discouraged for collections which will be included in the Ansible Community Distribution.

The categories are very similar to the ones in the `Ansible-base changelog fragments <https://docs.ansible.com/ansible/latest/community/development_process.html#changelogs-how-to>`_. In fact, they are the same, except that there are three new categories: ``breaking_changes``, ``security_fixes`` and ``trivial``.

The full list of categories is:

**release_summary**
  This is a special section: as opposed to a list of strings, it accepts one string. This string will be inserted at the top of the changelog entry for the current version, before any section. There can only be one fragment with a ``release_summary`` section. In Ansible-base, this is used for stating the release date and for linking to the porting guide (`example <https://github.com/ansible/ansible/blob/stable-2.9/changelogs/fragments/v2.9.0_summary.yaml>`_, `result <https://github.com/ansible/ansible/blob/stable-2.9/changelogs/CHANGELOG-v2.9.rst#id23>`_).

**breaking_changes**
  This (new) category should list all changes to features which absolutely require attention from users when upgrading, because an existing behavior is changed. This is mostly what Ansible's Porting Guide used to describe. This section should only appear in a initial major release (`x.0.0`) according to semantic versioning.

**major_changes**
  This category contains major changes to the collection. It should only contain a few items per major version, describing high-level changes. This section should not appear in patch releases according to semantic versioning.

**minor_changes**
  This category should mention all new features, like plugin or module options. This section should not appear in patch releases according to semantic versioning.

**removed_features**
  This category should mention all modules, plugins and features that have been removed in this release. This section should only appear in a initial major release (`x.0.0`) according to semantic versioning.

**deprecated_features**
  This category should contain all modules, plugins and features which have been deprecated and will be removed in a future release. This section should not appear in patch releases according to semantic versioning.

**security_fixes**
  This category should mention all security relevant fixes, including CVEs if available.

**bugfixes**
  This category should be a list of all bug fixes which fix a bug that was present in a previous version.

**known_issues**
  This category should mention known issues that are currently not fixed or will not be fixed.

**trivial**
  This category will **not be shown** in the changelog. It can be used to describe changes that are not touching user-facing code, like changes in tests. This is useful if every PR is required to have a changelog fragment.

Examples
--------

A guide on how to write changelog fragments can be found in the `Ansible docs <https://docs.ansible.com/ansible/devel/community/development_process.html#changelogs-how-to>`_.

Example of a regular changelog fragment::

    bugfixes:
      - docker_container - wait for removal of container if docker API returns early
        (https://github.com/ansible/ansible/issues/65811).

The filename in this case was ``changelogs/fragments/65854-docker_container-wait-for-removal.yml``, because this was implemented in `PR #65854 in ansible/ansible <https://github.com/ansible/ansible/pull/65854>`_.

A fragment can also contain multiple sections, or multiple entries in one section::

    deprecated_features:
    - docker_container - the ``trust_image_content`` option will be removed. It has always been ignored by the module.
    - docker_stack - the return values ``err`` and ``out`` have been deprecated. Use ``stdout`` and ``stderr`` from now on instead.

    breaking_changes:
    - "docker_container - no longer passes information on non-anonymous volumes or binds as ``Volumes`` to the Docker daemon. This increases compatibility with the ``docker`` CLI program. Note that if you specify ``volumes: strict`` in ``comparisons``, this could cause existing containers created with docker_container from Ansible 2.9 or earlier to restart."

The ``release_summary`` section is special, in that it doesn't contain a list of strings, but a string, and that only one such entry can be shown in the changelog of a release. Usually for every release (pre-release or regular release), at most one fragment is added which contains a ``release_summary``, and this is only done by the person doing the release. The ``release_summary`` should include some global information on the release; for example, in `Ansible's changelog <https://github.com/ansible/ansible/blob/stable-2.9/changelogs/CHANGELOG-v2.9.rst#release-summary>`_, it always mentions the release date and links to the porting guide.

An example of how a fragment with ``release_summary`` could look like is ``changelogs/fragments/0.2.0.yml`` from community.general::

    release_summary: |
      This is the first proper release of the ``community.general`` collection on 2020-06-20.
      The changelog describes all changes made to the modules and plugins included in this collection since Ansible 2.9.0.

Porting Guide Entries
=====================

The following sections are considered as the Porting Guide of the collection. For collections included in Ansible, these will be inserted into Ansible's Porting Guide:

* major_changes
* breaking_changes
* deprecated_features
* removed_features 

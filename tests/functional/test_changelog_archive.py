# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test changelog functionality: keep_fragments and archiving
"""

import os

from typing import List, Optional

import mock

from antsibull_changelog.config import PathsConfig

from fixtures import collection_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin


def test_changelog_release_keep_fragments(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.config.changelog_filename_version_depth = 2
    collection_changelog.config.keep_fragments = True
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])
    collection_changelog.set_plugin_cache('1.0.0', {})

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == []

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.0 Release Notes
=========================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.
''')

    # Modify fragment
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option!'])

    # Refresh
    assert collection_changelog.run_tool('generate', ['-v', '--refresh-fragments']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.0 Release Notes
=========================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option!
- test - has a new option ``foo``.
''')


def test_changelog_release_remove_fragments(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.config.changelog_filename_version_depth = 2
    collection_changelog.config.keep_fragments = False
    collection_changelog.config.archive_path_template = None
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])
    collection_changelog.set_plugin_cache('1.0.0', {})

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.0.0.yml',
        'changelogs/fragments/baz-new-option.yaml',
        'changelogs/fragments/test-new-option.yml',
    ]
    assert diff.changed_files == []

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.0 Release Notes
=========================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.
''')

    # Refresh should be ignored
    assert collection_changelog.run_tool('generate', ['-v', '--refresh-fragments']) == 0
    assert collection_changelog.diff().unchanged

    # Add fragment with same filename, but different content
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz - do something crazy.'])
    collection_changelog.set_plugin_cache('1.1.0', {})

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--version', '1.1.0', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/baz-new-option.yaml',
    ]
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.1 Release Notes
=========================

.. contents:: Topics


v1.1.0
======

Minor Changes
-------------

- baz - do something crazy.

v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.
''')

    # Set prevent_known_fragments to True
    collection_changelog.config.prevent_known_fragments = True
    collection_changelog.set_config(collection_changelog.config)

    # Add fragment with same filename, but different content
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz - do something even more crazy.'])
    collection_changelog.set_plugin_cache('1.2.0', {})

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--version', '1.2.0', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.2 Release Notes
=========================

.. contents:: Topics


v1.2.0
======

v1.1.0
======

Minor Changes
-------------

- baz - do something crazy.

v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.
''')


def test_changelog_release_archive_fragments(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.config.changelog_filename_version_depth = 2
    collection_changelog.config.keep_fragments = False
    collection_changelog.config.archive_path_template = '.archive/v{version}'
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])
    collection_changelog.set_plugin_cache('1.0.0', {})

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == ['.archive', '.archive/v1.0.0']
    assert diff.added_files == [
        '.archive/v1.0.0/1.0.0.yml',
        '.archive/v1.0.0/baz-new-option.yaml',
        '.archive/v1.0.0/test-new-option.yml',
        'CHANGELOG.rst',
        'changelogs/changelog.yaml',
    ]
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.0.0.yml',
        'changelogs/fragments/baz-new-option.yaml',
        'changelogs/fragments/test-new-option.yml',
    ]
    assert diff.changed_files == []

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.0 Release Notes
=========================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.
''')

    # Modify archived fragment
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option!'],
        fragment_dir='.archive/v1.0.0')

    # Refresh
    assert collection_changelog.run_tool('generate', ['-v', '--refresh-fragments']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.0 Release Notes
=========================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option!
- test - has a new option ``foo``.
''')

    # Modify archived fragment back
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'],
        fragment_dir='.archive/v1.0.0')

    # Refresh with --without-archives should be ignored
    assert collection_changelog.run_tool('generate', ['-v', '--refresh-fragments', 'without-archives']) == 0
    assert collection_changelog.diff().unchanged

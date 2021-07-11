# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test basic changelog functionality: Ansible collections
"""

import os

import mock

from fixtures import other_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin

import antsibull_changelog.ansible  # noqa: F401; pylint: disable=unused-variable


def test_changelog_init(  # pylint: disable=redefined-outer-name
        other_changelog):  # noqa: F811
    # If we do not specify --is-other-project, it should error out
    assert other_changelog.run_tool('init', [other_changelog.paths.base_dir]) == 5

    # If we do specify it, it just work
    assert other_changelog.run_tool('init', [other_changelog.paths.base_dir, '--is-other-project']) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == ['changelogs', 'changelogs/fragments']
    assert diff.added_files == ['changelogs/config.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == []

    config = diff.parse_yaml('changelogs/config.yaml')
    assert config['notesdir'] == 'fragments'
    assert config['changes_file'] == 'changelog.yaml'
    assert config['changelog_filename_template'] == '../CHANGELOG.rst'
    assert config['is_other_project'] is True
    assert config['use_semantic_versioning'] is True
    assert config['title'] == 'Project'


def test_changelog_release_empty(  # pylint: disable=redefined-outer-name
        other_changelog):  # noqa: F811
    other_changelog.set_config(other_changelog.config)
    other_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    other_changelog.add_fragment_line(
        'trivial.yml', 'trivial', 'This should not show up in the changelog.')

    # If we do not pass --version, will fail
    assert other_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 5

    # If we pass --version, will succeed
    assert other_changelog.run_tool('release', ['-v', '--date', '2020-01-02', '--version', '1.0.0']) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == ['changelogs/fragments/1.0.0.yml', 'changelogs/fragments/trivial.yml']
    assert diff.changed_files == []

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0']
    assert changelog['releases']['1.0.0']['release_date'] == '2020-01-02'
    assert changelog['releases']['1.0.0']['changes'] == {
        'release_summary': 'This is the first proper release.'
    }
    assert changelog['releases']['1.0.0']['fragments'] == ['1.0.0.yml', 'trivial.yml']
    assert 'modules' not in changelog['releases']['1.0.0']
    assert 'plugins' not in changelog['releases']['1.0.0']
    assert 'objects' not in changelog['releases']['1.0.0']
    assert 'codename' not in changelog['releases']['1.0.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==============================
A Random Project Release Notes
==============================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.
''')

    assert other_changelog.run_tool('generate', ['-v', '--refresh']) == 0
    assert other_changelog.diff().unchanged

    assert other_changelog.run_tool('release', ['-v', '--codename', 'primetime', '--date', '2020-01-03', '--version', '1.0.0']) == 0
    assert other_changelog.diff().unchanged

    assert other_changelog.run_tool('release', ['-v', '--codename', 'primetime', '--date', '2020-01-03', '--version', '1.0.0', '--update-existing']) == 0
    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['releases']['1.0.0']['release_date'] == '2020-01-03'
    assert changelog['releases']['1.0.0']['codename'] == 'primetime'

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==========================================
A Random Project "primetime" Release Notes
==========================================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.
''')

    # Version 1.1.0

    assert other_changelog.run_tool('release', ['-v', '--date', '2020-02-29', '--version', '1.1.0']) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0', '1.1.0']
    assert changelog['releases']['1.1.0']['release_date'] == '2020-02-29'
    assert 'changes' not in changelog['releases']['1.1.0']
    assert 'fragments' not in changelog['releases']['1.1.0']
    assert 'modules' not in changelog['releases']['1.1.0']
    assert 'plugins' not in changelog['releases']['1.1.0']
    assert 'objects' not in changelog['releases']['1.1.0']
    assert 'codename' not in changelog['releases']['1.1.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==============================
A Random Project Release Notes
==============================

.. contents:: Topics


v1.1.0
======

v1.0.0
======

Release Summary
---------------

This is the first proper release.
''')

    assert other_changelog.run_tool('generate', ['-v', '--refresh']) == 0
    assert other_changelog.diff().unchanged


def test_changelog_release_simple(  # pylint: disable=redefined-outer-name
        other_changelog):  # noqa: F811
    other_changelog.config.changelog_filename_version_depth = 2
    other_changelog.config.use_semantic_versioning = True
    other_changelog.set_config(other_changelog.config)
    other_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    other_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    other_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])

    # Lint fragments
    assert other_changelog.run_tool('lint', ['-vv']) == 0

    # Release
    assert other_changelog.run_tool('release', ['-v', '--date', '2020-01-02', '--version', '1.0.0']) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.0.0.yml',
        'changelogs/fragments/baz-new-option.yaml',
        'changelogs/fragments/test-new-option.yml',
    ]
    assert diff.changed_files == []

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0']
    assert changelog['releases']['1.0.0']['release_date'] == '2020-01-02'
    assert changelog['releases']['1.0.0']['changes'] == {
        'release_summary': 'This is the first proper release.',
        'minor_changes': [
            'baz lookup - no longer ignores the ``bar`` option.',
            'test - has a new option ``foo``.',
        ],
    }
    assert changelog['releases']['1.0.0']['fragments'] == [
        '1.0.0.yml',
        'baz-new-option.yaml',
        'test-new-option.yml',
    ]
    assert 'modules' not in changelog['releases']['1.0.0']
    assert 'plugins' not in changelog['releases']['1.0.0']
    assert 'codename' not in changelog['releases']['1.0.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==================================
A Random Project 1.0 Release Notes
==================================

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

    # Check that regenerate doesn't change anything
    assert other_changelog.run_tool('generate', ['-v']) == 0
    assert other_changelog.diff().unchanged

    # Add another fragment
    other_changelog.add_fragment_line(
        'test-new-fragment.yml', 'minor_changes', ['Another new fragment.'])

    # Check that regenerate without --refresh* doesn't change anything
    assert other_changelog.run_tool('generate', ['-v']) == 0
    assert other_changelog.diff().unchanged

    # Check that regenerate with --refresh-fragments does not change
    assert other_changelog.run_tool('generate', ['-v', '--refresh-fragments']) == 0

    diff = other_changelog.diff()
    assert diff.unchanged

    # Check that regenerate with --refresh-plugins does not change
    assert other_changelog.run_tool('generate', ['-v', '--refresh-plugins']) == 0

    diff = other_changelog.diff()
    assert diff.unchanged

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert 'modules' not in changelog['releases']['1.0.0']
    assert 'plugins' not in changelog['releases']['1.0.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==================================
A Random Project 1.0 Release Notes
==================================

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

    # Prepare 1.1.0 beta 1
    other_changelog.add_fragment_line(
        '1.1.0-beta-1.yml', 'release_summary', 'Beta of 1.1.0.')

    # Release 1.1.0-beta-1
    assert other_changelog.run_tool('release', [
        '-v',
        '--date', '2020-02-14',
        '--version', '1.1.0-beta-1',
    ]) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.1.0-beta-1.yml',
        'changelogs/fragments/test-new-fragment.yml',
    ]
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0', '1.1.0-beta-1']
    assert changelog['releases']['1.1.0-beta-1']['release_date'] == '2020-02-14'
    assert changelog['releases']['1.1.0-beta-1']['changes'] == {
        'release_summary': 'Beta of 1.1.0.',
        'minor_changes': [
            'Another new fragment.',
        ],
    }
    assert changelog['releases']['1.1.0-beta-1']['fragments'] == [
        '1.1.0-beta-1.yml',
        'test-new-fragment.yml',
    ]
    assert 'modules' not in changelog['releases']['1.1.0-beta-1']
    assert 'plugins' not in changelog['releases']['1.1.0-beta-1']
    assert 'objects' not in changelog['releases']['1.1.0-beta-1']
    assert 'codename' not in changelog['releases']['1.1.0-beta-1']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==================================
A Random Project 1.1 Release Notes
==================================

.. contents:: Topics


v1.1.0-beta-1
=============

Release Summary
---------------

Beta of 1.1.0.

Minor Changes
-------------

- Another new fragment.

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

    # Prepare 1.1.0
    other_changelog.add_fragment_line(
        '1.1.0.yml', 'release_summary', 'Final release of 1.1.0.')
    other_changelog.add_fragment_line(
        'minorchange.yml', 'minor_changes', ['A minor change.'])
    other_changelog.add_fragment_line(
        'bugfix.yml', 'bugfixes', ['A bugfix.'])

    # Lint fragments
    assert other_changelog.run_tool('lint', [
        '-vvv',
    ]) == 0

    # Final release 1.1.0
    assert other_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-02-29',
        '--version', '1.1.0',
    ]) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.1.0.yml',
        'changelogs/fragments/bugfix.yml',
        'changelogs/fragments/minorchange.yml',
    ]
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0', '1.1.0', '1.1.0-beta-1']
    assert changelog['releases']['1.1.0']['release_date'] == '2020-02-29'
    assert changelog['releases']['1.1.0']['changes'] == {
        'release_summary': 'Final release of 1.1.0.',
        'bugfixes': ['A bugfix.'],
        'minor_changes': ['A minor change.'],
    }
    assert changelog['releases']['1.1.0']['fragments'] == [
        '1.1.0.yml',
        'bugfix.yml',
        'minorchange.yml',
    ]
    assert 'modules' not in changelog['releases']['1.1.0']
    assert 'plugins' not in changelog['releases']['1.1.0']
    assert 'objects' not in changelog['releases']['1.1.0']
    assert 'codename' not in changelog['releases']['1.1.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==================================
A Random Project 1.1 Release Notes
==================================

.. contents:: Topics


v1.1.0
======

Release Summary
---------------

Final release of 1.1.0.

Minor Changes
-------------

- A minor change.
- Another new fragment.

Bugfixes
--------

- A bugfix.

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

    # Final release 1.1.0 - should not change
    assert other_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-03-01',
        '--version', '1.1.0',
    ]) == 0

    assert other_changelog.diff().unchanged

    # Prepare 1.2.0
    other_changelog.add_fragment_line(
        '1.2.0.yml', 'release_summary', 'Release of 1.2.0.')

    # Release 1.2.0
    assert other_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-03-01',
        '--version', '1.2.0',
    ]) == 0

    diff = other_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == ['changelogs/fragments/1.2.0.yml']
    assert diff.changed_files == ['CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0', '1.1.0', '1.1.0-beta-1', '1.2.0']
    assert changelog['releases']['1.2.0']['release_date'] == '2020-03-01'
    assert changelog['releases']['1.2.0']['changes'] == {
        'release_summary': 'Release of 1.2.0.',
    }
    assert changelog['releases']['1.2.0']['fragments'] == ['1.2.0.yml']
    assert 'modules' not in changelog['releases']['1.2.0']
    assert 'plugins' not in changelog['releases']['1.2.0']
    assert 'objects' not in changelog['releases']['1.2.0']
    assert 'codename' not in changelog['releases']['1.2.0']

    assert diff.file_contents['CHANGELOG.rst'].decode('utf-8') == (
        r'''==================================
A Random Project 1.2 Release Notes
==================================

.. contents:: Topics


v1.2.0
======

Release Summary
---------------

Release of 1.2.0.

v1.1.0
======

Release Summary
---------------

Final release of 1.1.0.

Minor Changes
-------------

- A minor change.
- Another new fragment.

Bugfixes
--------

- A bugfix.

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

    # Release 1.2.0 - should not change
    assert other_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-03-02',
        '--version', '1.2.0',
    ]) == 0

    assert other_changelog.diff().unchanged

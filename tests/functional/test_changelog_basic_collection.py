# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test basic changelog functionality: Ansible collections
"""

import os

from typing import List

import mock

from antsibull_changelog.config import PathsConfig

from fixtures import collection_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin


def test_changelog_init(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    assert collection_changelog.run_tool('init', [collection_changelog.paths.base_dir]) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == ['changelogs', 'changelogs/fragments']
    assert diff.added_files == ['changelogs/config.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == []

    config = diff.parse_yaml('changelogs/config.yaml')
    assert config['notesdir'] == 'fragments'
    assert config['changes_file'] == 'changelog.yaml'
    assert config['changelog_filename_template'] == 'CHANGELOG.rst'
    assert 'release_tag_re' not in config
    assert 'pre_release_tag_re' not in config
    assert config['title'] == collection_changelog.collection_name.title()


def test_changelog_release_empty(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.set_plugin_cache('1.0.0', {})

    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == ['changelogs/fragments/1.0.0.yml']
    assert diff.changed_files == []

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0']
    assert changelog['releases']['1.0.0']['release_date'] == '2020-01-02'
    assert changelog['releases']['1.0.0']['changes'] == {
        'release_summary': 'This is the first proper release.'
    }
    assert changelog['releases']['1.0.0']['fragments'] == ['1.0.0.yml']
    assert 'modules' not in changelog['releases']['1.0.0']
    assert 'plugins' not in changelog['releases']['1.0.0']
    assert 'codename' not in changelog['releases']['1.0.0']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''=====================
Ansible Release Notes
=====================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.
''')

    assert collection_changelog.run_tool('generate', ['-v', '--refresh']) == 0
    assert collection_changelog.diff().unchanged

    # Version 1.1.0

    collection_changelog.set_galaxy({
        'version': '1.1.0',
    })
    collection_changelog.set_plugin_cache('1.1.0', {})

    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-02-29']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['1.0.0', '1.1.0']
    assert changelog['releases']['1.1.0']['release_date'] == '2020-02-29'
    assert 'changes' not in changelog['releases']['1.1.0']
    assert 'fragments' not in changelog['releases']['1.1.0']
    assert 'modules' not in changelog['releases']['1.1.0']
    assert 'plugins' not in changelog['releases']['1.1.0']
    assert 'codename' not in changelog['releases']['1.1.0']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''=====================
Ansible Release Notes
=====================

.. contents:: Topics


v1.1.0
======

v1.0.0
======

Release Summary
---------------

This is the first proper release.
''')

    assert collection_changelog.run_tool('generate', ['-v', '--refresh']) == 0
    assert collection_changelog.diff().unchanged


def test_changelog_release_simple(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.config.changelog_filename_version_depth = 2
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])
    collection_changelog.set_plugin_cache('1.0.0', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a test module',
                'namespace': '',
                'version_added': '1.0.0',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
                'version_added': '1.0.0',
            },
            'baz': {
                'name': 'baz',
                'description': 'Has already been here',
                'namespace': None,
                'version_added': None,
            },
            'boom': {
                'name': 'boom',
                'description': 'Something older',
                'namespace': None,
                'version_added': '0.5.0',
            },
        },
    })

    # Lint fragments
    assert collection_changelog.run_tool('lint', ['-vv']) == 0

    # Release
    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']
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
    assert changelog['releases']['1.0.0']['modules'] == [
        {
            'name': 'test',
            'description': 'This is a test module',
            'namespace': '',
        },
    ]
    assert changelog['releases']['1.0.0']['plugins'] == {
        'lookup': [
            {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
            },
        ],
    }
    assert 'codename' not in changelog['releases']['1.0.0']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
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

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo bar lookup

New Modules
-----------

- test - This is a test module
''')

    # Check that regenerate doesn't change anything
    assert collection_changelog.run_tool('generate', ['-v']) == 0
    assert collection_changelog.diff().unchanged

    # Update plugin descriptions
    collection_changelog.set_plugin_cache('1.0.0', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '1.0.0',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '1.0.0',
            },
            'baz': {
                'name': 'baz',
                'description': 'Has already been here before',
                'namespace': None,
                'version_added': None,
            },
            'boom': {
                'name': 'boom',
                'description': 'Something older',
                'namespace': None,
                'version_added': '0.5.0',
            },
        },
    })

    # Add another fragment
    collection_changelog.add_fragment_line(
        'test-new-fragment.yml', 'minor_changes', ['Another new fragment.'])

    # Check that regenerate without --refresh doesn't change anything
    assert collection_changelog.run_tool('generate', ['-v']) == 0
    assert collection_changelog.diff().unchanged

    # Check that regenerate with --refresh changes
    assert collection_changelog.run_tool('generate', ['-v', '--refresh']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['releases']['1.0.0']['modules'] == [
        {
            'name': 'test',
            'description': 'This is a TEST module',
            'namespace': '',
        },
    ]
    assert changelog['releases']['1.0.0']['plugins'] == {
        'lookup': [
            {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
            },
        ],
    }

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
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

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Update plugin descriptions for 1.1.0 beta 1
    collection_changelog.set_plugin_cache('1.1.0-beta-1', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '1.0.0',
            },
            'test_new': {
                'name': 'test_new',
                'description': 'This is ANOTHER test module',
                'namespace': '',
                'version_added': '1.1.0',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '1.0.0',
            },
            'baz': {
                'name': 'baz',
                'description': 'Has already been here before',
                'namespace': None,
                'version_added': None,
            },
            'boom': {
                'name': 'boom',
                'description': 'Something older',
                'namespace': None,
                'version_added': '0.5.0',
            },
        },
    })

    collection_changelog.add_fragment_line(
        '1.1.0-beta-1.yml', 'release_summary', 'Beta of 1.1.0.')

    # Release 1.1.0-beta-1
    assert collection_changelog.run_tool('release', [
        '-v',
        '--date', '2020-02-14',
        '--version', '1.1.0-beta-1',
    ]) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.1.0-beta-1.yml',
        'changelogs/fragments/test-new-fragment.yml',
    ]
    assert diff.changed_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']

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
    assert changelog['releases']['1.1.0-beta-1']['modules'] == [
        {
            'name': 'test_new',
            'description': 'This is ANOTHER test module',
            'namespace': '',
        },
    ]
    assert 'plugins' not in changelog['releases']['1.1.0-beta-1']
    assert 'codename' not in changelog['releases']['1.1.0-beta-1']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.1 Release Notes
=========================

.. contents:: Topics


v1.1.0-beta-1
=============

Release Summary
---------------

Beta of 1.1.0.

Minor Changes
-------------

- Another new fragment.

New Modules
-----------

- test_new - This is ANOTHER test module

v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Update plugin descriptions for 1.1.0
    collection_changelog.set_plugin_cache('1.1.0', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '1.0.0',
            },
            'test_new': {
                'name': 'test_new',
                'description': 'This is ANOTHER test module',
                'namespace': '',
                'version_added': '1.1.0',
            },
            'test_new2': {
                'name': 'test_new2',
                'description': 'This is ANOTHER test module!!!11',
                'namespace': '',
                'version_added': '1.1.0',
            },
            'test_new3': {
                'name': 'test_new3',
                'description': 'This is yet another test module.',
                'namespace': '',
                'version_added': '1.1.0',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '1.0.0',
            },
            'baz': {
                'name': 'baz',
                'description': 'Has already been here before',
                'namespace': None,
                'version_added': None,
            },
            'boom': {
                'name': 'boom',
                'description': 'Something older',
                'namespace': None,
                'version_added': '0.5.0',
            },
        },
    })

    collection_changelog.add_fragment_line(
        '1.1.0.yml', 'release_summary', 'Final release of 1.1.0.')
    collection_changelog.add_fragment_line(
        'minorchange.yml', 'minor_changes', ['A minor change.'])
    collection_changelog.add_fragment_line(
        'bugfix.yml', 'bugfixes', ['A bugfix.'])

    # Final release 1.1.0
    assert collection_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-02-29',
        '--version', '1.1.0',
    ]) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == [
        'changelogs/fragments/1.1.0.yml',
        'changelogs/fragments/bugfix.yml',
        'changelogs/fragments/minorchange.yml',
    ]
    assert diff.changed_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']

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
    assert changelog['releases']['1.1.0']['modules'] == [
        {
            'name': 'test_new2',
            'description': 'This is ANOTHER test module!!!11',
            'namespace': '',
        },
        {
            'name': 'test_new3',
            'description': 'This is yet another test module.',
            'namespace': '',
        },
    ]
    assert 'plugins' not in changelog['releases']['1.1.0']
    assert 'codename' not in changelog['releases']['1.1.0']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''=========================
Ansible 1.1 Release Notes
=========================

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

New Modules
-----------

- test_new - This is ANOTHER test module
- test_new2 - This is ANOTHER test module!!!11
- test_new3 - This is yet another test module.

v1.0.0
======

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.
- test - has a new option ``foo``.

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Final release 1.1.0 - should not change
    assert collection_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-03-01',
        '--version', '1.1.0',
    ]) == 0

    assert collection_changelog.diff().unchanged


def test_changelog_release_simple_no_galaxy(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.config.title = 'Test Collection'
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])

    # If we don't specify all options, the call will fail
    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 5
    assert collection_changelog.run_tool('release', [  # without --version
        '-v',
        '--date', '2020-01-02',
        '--is-collection', 'true',
        '--collection-namespace', 'cloud',
        '--collection-name', 'sky',
        '--collection-flatmap', 'yes',
    ]) == 5
    assert collection_changelog.run_tool('release', [  # without --is-collection
        '-v',
        '--date', '2020-01-02',
        '--version', '1.0.0',
        '--collection-namespace', 'cloud',
        '--collection-name', 'sky',
        '--collection-flatmap', 'yes',
    ]) == 5
    assert collection_changelog.run_tool('release', [  # without --collection-namespace
        '-v',
        '--date', '2020-01-02',
        '--version', '1.0.0',
        '--is-collection', 'true',
        '--collection-name', 'sky',
        '--collection-flatmap', 'yes',
    ]) == 5
    assert collection_changelog.run_tool('release', [  # without --collection-name
        '-v',
        '--date', '2020-01-02',
        '--version', '1.0.0',
        '--is-collection', 'true',
        '--collection-namespace', 'cloud',
        '--collection-flatmap', 'yes',
    ]) == 5
    assert collection_changelog.run_tool('release', [  # without --collection-flatmap
        '-v',
        '--date', '2020-01-02',
        '--version', '1.0.0',
        '--is-collection', 'true',
        '--collection-namespace', 'cloud',
        '--collection-name', 'sky',
    ]) == 5

    # Add plugin cache content
    collection_changelog.set_plugin_cache('1.0.0', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a test module',
                'namespace': '',
                'version_added': '1.0.0',
            },
            'test1': {
                'name': 'test1',
                'description': 'This is a test module',
                'namespace': 'test',
                'version_added': '1.0.0',
            },
            'test2': {
                'name': 'test2',
                'description': 'This is a test module',
                'namespace': 'test.foo',
                'version_added': '1.0.0',
            },
            'test3': {
                'name': 'test3',
                'description': 'This is a test module',
                'namespace': 'test.bar',
                'version_added': '1.0.0',
            },
            'test4': {
                'name': 'test4',
                'description': 'This is a test module',
                'namespace': 'foo',
                'version_added': '1.0.0',
            },
            'test5': {
                'name': 'test5',
                'description': 'This is a test module',
                'namespace': 'bar.baz',
                'version_added': '1.0.0',
            },
            'test6': {
                'name': 'test6',
                'description': 'This is a test module',
                'namespace': 'foo.bar.baz',
                'version_added': '1.0.0',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
                'version_added': '1.0.0',
            },
            'baz': {
                'name': 'baz',
                'description': 'Has already been here',
                'namespace': None,
                'version_added': None,
            },
        },
    })

    # If we specify all options, the call will succeed
    assert collection_changelog.run_tool('release', [
        '-v',
        '--date', '2020-01-02',
        '--version', '1.0.0',
        '--is-collection', 'true',
        # The following two options are not needed since the tool doesn't have to scan for plugins:
        # '--collection-namespace', 'cloud',
        # '--collection-name', 'sky',
        '--collection-flatmap', 'yes',
    ]) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['changelogs/CHANGELOG.rst', 'changelogs/changelog.yaml']
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
    assert changelog['releases']['1.0.0']['modules'] == [
        {
            'name': 'test',
            'description': 'This is a test module',
            'namespace': '',
        },
        {
            'name': 'test1',
            'description': 'This is a test module',
            'namespace': 'test',
        },
        {
            'name': 'test2',
            'description': 'This is a test module',
            'namespace': 'test.foo',
        },
        {
            'name': 'test3',
            'description': 'This is a test module',
            'namespace': 'test.bar',
        },
        {
            'name': 'test4',
            'description': 'This is a test module',
            'namespace': 'foo',
        },
        {
            'name': 'test5',
            'description': 'This is a test module',
            'namespace': 'bar.baz',
        },
        {
            'name': 'test6',
            'description': 'This is a test module',
            'namespace': 'foo.bar.baz',
        },
    ]
    assert changelog['releases']['1.0.0']['plugins'] == {
        'lookup': [
            {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
            },
        ],
    }
    assert 'codename' not in changelog['releases']['1.0.0']

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''=============================
Test Collection Release Notes
=============================

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

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo bar lookup

New Modules
-----------

- test - This is a test module

Bar
~~~

baz
^^^

- test5 - This is a test module

Foo
~~~

- test4 - This is a test module

bar.baz
^^^^^^^

- test6 - This is a test module

Test
~~~~

- test1 - This is a test module

bar
^^^

- test3 - This is a test module

foo
^^^

- test2 - This is a test module
''')


def fake_ansible_doc_collection(paths: PathsConfig, plugin_type: str,
                                plugin_names: List[str]) -> dict:
    """
    Fake ansible-doc mock for collection.
    """
    if plugin_type == 'callback':
        assert sorted(plugin_names) == ['acme.test.test_callback']
        return {
            'acme.test.test_callback': {
                'doc': {
                    'author': ['Someone else'],
                    'description': ['This is a relatively new callback added before.'],
                    'filename': os.path.join(paths.base_dir, 'plugins',
                                             'callback', 'test_callback.py'),
                    'name': 'test_callback',
                    'options': {},
                    'short_description': 'A not so old callback',
                    'version_added': '0.5.0',
                },
                'examples': '# Some examples\n',
                'metadata': {
                    'status': ['preview'],
                    'supported_by': 'community',
                },
                'return': {},
            }
        }
    if plugin_type == 'module':
        assert sorted(plugin_names) == ['acme.test.cloud.sky.old_module', 'acme.test.test_module']
        return {
            'acme.test.cloud.sky.old_module': {
                'doc': {
                    'author': ['Elder'],
                    'description': ['This is an old module.'],
                    'filename': os.path.join(paths.base_dir, 'plugins', 'modules',
                                             'cloud', 'sky', 'old_module.py'),
                    'name': 'old_module',
                    'options': {},
                    'short_description': 'An old module',
                },
                'examples': '# Some examples\n',
                'metadata': {
                    'status': ['preview'],
                    'supported_by': 'community',
                },
                'return': {},
            },
            'acme.test.test_module': {
                'doc': {
                    'author': ['Someone'],
                    'description': ['This is a test module.'],
                    'filename': os.path.join(paths.base_dir, 'plugins',
                                             'modules', 'test_module.py'),
                    'name': 'test_module',
                    'options': {},
                    'short_description': 'A test module',
                    'version_added': '1.0.0',
                },
                'examples': '',
                'metadata': {
                    'status': ['preview'],
                    'supported_by': 'community',
                },
                'return': {},
            }
        }
    raise Exception(
        'ansible-doc should not be called with plugin_type == "{0}"'.format(plugin_type))


@mock.patch('antsibull_changelog.plugins.run_ansible_doc', fake_ansible_doc_collection)
def test_changelog_release_plugin_cache(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_galaxy({
        'version': '1.0.0',
    })
    collection_changelog.config.title = 'My Amazing Collection'
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_plugin('module', 'test_module.py', create_plugin(
        DOCUMENTATION={
            'name': 'test_module',
            'short_description': 'A test module',
            'version_added': '1.0.0',
            'description': ['This is a test module.'],
            'author': ['Someone'],
            'options': {},
        },
        EXAMPLES='',
        RETURN={},
    ))
    collection_changelog.add_plugin('module', '__init__.py', create_plugin(
        DOCUMENTATION={
            'name': 'bad_module',
            'short_description': 'Bad module',
            'description': ['This should be ignored, not found as a module!.'],
            'author': ['badguy'],
            'options': {},
        },
        EXAMPLES='# Some examples\n',
        RETURN={},
    ), subdirs=['cloud'])
    collection_changelog.add_plugin('module', 'old_module.py', create_plugin(
        DOCUMENTATION={
            'name': 'old_module',
            'short_description': 'An old module',
            'description': ['This is an old module.'],
            'author': ['Elder'],
            'options': {},
        },
        EXAMPLES='# Some examples\n',
        RETURN={},
    ), subdirs=['cloud', 'sky'])
    collection_changelog.add_plugin('module', 'bad_module2', create_plugin(
        DOCUMENTATION={
            'name': 'bad_module2',
            'short_description': 'An bad module',
            'description': ['Shold not be found either.'],
            'author': ['Elder'],
            'options': {},
        },
        EXAMPLES='# Some examples\n',
        RETURN={},
    ), subdirs=['cloud', 'sky'])
    collection_changelog.add_plugin('callback', 'test_callback.py', create_plugin(
        DOCUMENTATION={
            'name': 'test_callback',
            'short_description': 'A not so old callback',
            'version_added': '0.5.0',
            'description': ['This is a relatively new callback added before.'],
            'author': ['Someone else'],
            'options': {},
        },
        EXAMPLES='# Some examples\n',
        RETURN={},
    ))
    collection_changelog.add_plugin('callback', 'test_callback2.py', create_plugin(
        DOCUMENTATION={
            'name': 'test_callback2',
            'short_description': 'This one should not be found.',
            'version_added': '2.9',
            'description': ['This is a relatively new callback added before.'],
            'author': ['Someone else'],
            'options': {},
        },
        EXAMPLES='# Some examples\n',
        RETURN={},
    ), subdirs=['dont', 'find', 'me'])

    assert collection_changelog.run_tool('release', ['-v', '--date', '2020-01-02']) == 0

    diff = collection_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == [
        'changelogs/.plugin-cache.yaml',
        'changelogs/CHANGELOG.rst',
        'changelogs/changelog.yaml',
    ]
    assert diff.removed_dirs == []
    assert diff.removed_files == ['changelogs/fragments/1.0.0.yml']
    assert diff.changed_files == []

    plugin_cache = diff.parse_yaml('changelogs/.plugin-cache.yaml')
    assert plugin_cache['version'] == '1.0.0'

    # Plugin cache: modules
    assert sorted(plugin_cache['plugins']['module']) == ['old_module', 'test_module']
    assert plugin_cache['plugins']['module']['old_module']['name'] == 'old_module'
    assert plugin_cache['plugins']['module']['old_module']['namespace'] == 'cloud.sky'
    assert plugin_cache['plugins']['module']['old_module']['description'] == 'An old module'
    assert plugin_cache['plugins']['module']['old_module']['version_added'] is None
    assert plugin_cache['plugins']['module']['test_module']['name'] == 'test_module'
    assert plugin_cache['plugins']['module']['test_module']['namespace'] == ''
    assert plugin_cache['plugins']['module']['test_module']['description'] == 'A test module'
    assert plugin_cache['plugins']['module']['test_module']['version_added'] == '1.0.0'

    # Plugin cache: callbacks
    assert sorted(plugin_cache['plugins']['callback']) == ['test_callback']
    assert plugin_cache['plugins']['callback']['test_callback']['name'] == 'test_callback'
    assert plugin_cache['plugins']['callback']['test_callback']['description'] == \
        'A not so old callback'
    assert plugin_cache['plugins']['callback']['test_callback']['version_added'] == '0.5.0'
    assert 'namespace' not in plugin_cache['plugins']['callback']['test_callback']

    # Changelog
    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert sorted(changelog['releases']) == ['1.0.0']
    assert changelog['releases']['1.0.0']['release_date'] == '2020-01-02'
    assert changelog['releases']['1.0.0']['changes'] == {
        'release_summary': 'This is the first proper release.'
    }
    assert changelog['releases']['1.0.0']['fragments'] == ['1.0.0.yml']
    assert len(changelog['releases']['1.0.0']['modules']) == 1
    assert changelog['releases']['1.0.0']['modules'][0]['name'] == 'test_module'
    assert changelog['releases']['1.0.0']['modules'][0]['namespace'] == ''
    assert changelog['releases']['1.0.0']['modules'][0]['description'] == 'A test module'
    assert 'version_added' not in changelog['releases']['1.0.0']['modules'][0]

    assert diff.file_contents['changelogs/CHANGELOG.rst'].decode('utf-8') == (
        r'''===================================
My Amazing Collection Release Notes
===================================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

This is the first proper release.

New Modules
-----------

- test_module - A test module
''')

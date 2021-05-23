# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test basic changelog functionality: Ansible Base 2.10+
"""

import os

import mock

from fixtures import ansible_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin


def test_changelog_release_ansible_empty(  # pylint: disable=redefined-outer-name
        ansible_changelog):  # noqa: F811
    ansible_config_contents = r'''
---
title: Ansible Base
release_tag_re: '(v(?:[\d.ab\-]|rc)+)'
pre_release_tag_re: '(?P<pre_release>(?:[ab]|rc)+\d*)$'
changes_file: changelog.yaml
changes_format: combined
keep_fragments: true
always_refresh: true
mention_ancestor: false
notesdir: fragments
prelude_section_name: release_summary
new_plugins_after_name: removed_features
sections:
- ['major_changes', 'Major Changes']
- ['minor_changes', 'Minor Changes']
- ['deprecated_features', 'Deprecated Features']
- ['removed_features', 'Removed Features (previously deprecated)']
- ['bugfixes', 'Bugfixes']
- ['known_issues', 'Known Issues']
'''
    ansible_changelog.set_config_raw(ansible_config_contents.encode('utf-8'))
    ansible_changelog.add_fragment_line(
        '2.10.yml', 'release_summary', 'This is the first proper release.')
    ansible_changelog.set_plugin_cache('2.10', {})

    assert ansible_changelog.run_tool('release', [
        '-v',
        '--date', '2020-01-02',
        '--version', '2.10',
        '--codename', 'meow'
    ]) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == []

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['2.10']
    assert changelog['releases']['2.10']['release_date'] == '2020-01-02'
    assert changelog['releases']['2.10']['changes'] == {
        'release_summary': 'This is the first proper release.',
    }
    assert changelog['releases']['2.10']['fragments'] == [
        '2.10.yml',
    ]
    assert 'modules' not in changelog['releases']['2.10']
    assert 'plugins' not in changelog['releases']['2.10']
    assert changelog['releases']['2.10']['codename'] == 'meow'

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''======================================
Ansible Base 2.10 "meow" Release Notes
======================================

.. contents:: Topics


v2.10
=====

Release Summary
---------------

This is the first proper release.
''')

    assert ansible_changelog.run_tool('generate', ['-v']) == 0
    assert ansible_changelog.diff().unchanged

    # Version 2.10.1

    ansible_changelog.set_plugin_cache('2.10.1', {})

    assert ansible_changelog.run_tool('release', [
        '-v',
        '--date', '2020-02-29',
        '--version', '2.10.1',
        '--codename', 'meow'
    ]) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['2.10', '2.10.1']
    assert changelog['releases']['2.10.1']['release_date'] == '2020-02-29'
    assert 'changes' not in changelog['releases']['2.10.1']
    assert 'fragments' not in changelog['releases']['2.10.1']
    assert 'modules' not in changelog['releases']['2.10.1']
    assert 'plugins' not in changelog['releases']['2.10.1']
    assert changelog['releases']['2.10.1']['codename'] == 'meow'

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''======================================
Ansible Base 2.10 "meow" Release Notes
======================================

.. contents:: Topics


v2.10.1
=======

v2.10
=====

Release Summary
---------------

This is the first proper release.
''')

    assert ansible_changelog.run_tool('generate', ['-v', '--refresh']) == 0
    assert ansible_changelog.diff().unchanged


def test_changelog_release_ansible_simple(  # pylint: disable=redefined-outer-name
        ansible_changelog):  # noqa: F811
    ansible_config_contents = r'''
---
title: Ansible Base
release_tag_re: '(v(?:[\d.ab\-]|rc)+)'
pre_release_tag_re: '(?P<pre_release>(?:[ab]|rc)+\d*)$'
changes_file: changelog.yaml
changes_format: combined
keep_fragments: true
always_refresh: true
mention_ancestor: false
notesdir: fragments
prelude_section_name: release_summary
new_plugins_after_name: removed_features
sections:
- ['major_changes', 'Major Changes']
- ['minor_changes', 'Minor Changes']
- ['deprecated_features', 'Deprecated Features']
- ['removed_features', 'Removed Features (previously deprecated)']
- ['bugfixes', 'Bugfixes']
- ['known_issues', 'Known Issues']
'''
    ansible_changelog.set_config_raw(ansible_config_contents.encode('utf-8'))
    ansible_changelog.add_fragment_line(
        '2.10.yml', 'release_summary', 'This is the first proper release.')
    ansible_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    ansible_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.\n\n'
         'We have multiple paragraphs!'])
    ansible_changelog.set_plugin_cache('2.10', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a test module',
                'namespace': '',
                'version_added': '2.10',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
                'version_added': '2.10',
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
                'version_added': '2.9',
            },
        },
    })

    assert ansible_changelog.run_tool('release', [
        '-v',
        '--date', '2020-01-02',
        '--version', '2.10',
        '--codename', 'meow'
    ]) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == []

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['2.10']
    assert changelog['releases']['2.10']['release_date'] == '2020-01-02'
    assert changelog['releases']['2.10']['changes'] == {
        'release_summary': 'This is the first proper release.',
        'minor_changes': [
            'baz lookup - no longer ignores the ``bar`` option.\n\nWe have multiple paragraphs!',
            'test - has a new option ``foo``.',
        ],
    }
    assert changelog['releases']['2.10']['fragments'] == [
        '2.10.yml',
        'baz-new-option.yaml',
        'test-new-option.yml',
    ]
    assert changelog['releases']['2.10']['modules'] == [
        {
            'name': 'test',
            'description': 'This is a test module',
            'namespace': '',
        },
    ]
    assert changelog['releases']['2.10']['plugins'] == {
        'lookup': [
            {
                'name': 'bar',
                'description': 'A foo bar lookup',
                'namespace': None,
            },
        ],
    }
    assert changelog['releases']['2.10']['codename'] == 'meow'

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''======================================
Ansible Base 2.10 "meow" Release Notes
======================================

.. contents:: Topics


v2.10
=====

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.

  We have multiple paragraphs!
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
    assert ansible_changelog.run_tool('generate', ['-v']) == 0
    assert ansible_changelog.diff().unchanged

    # Update plugin descriptions
    ansible_changelog.set_plugin_cache('2.10', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '2.10',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '2.10',
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
                'version_added': '2.9',
            },
        },
    })

    # Update existing changelog fragment.
    ansible_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.\n\n'
         'We have multiple paragraphs in this fragment.'])

    # Remove existing changelog fragment
    ansible_changelog.remove_fragment('test-new-option.yml')

    # Add another fragment
    ansible_changelog.add_fragment_line(
        'test-new-fragment.yml', 'minor_changes', ['Another new fragment.'])

    # Check that regenerate without --refresh changes
    # (since we specified always_refresh in config)
    assert ansible_changelog.run_tool('generate', ['-v']) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['releases']['2.10']['changes'] == {
        'release_summary': 'This is the first proper release.',
        'minor_changes': [
            'baz lookup - no longer ignores the ``bar`` option.\n\n'
            'We have multiple paragraphs in this fragment.',
        ],
    }
    assert changelog['releases']['2.10']['modules'] == [
        {
            'name': 'test',
            'description': 'This is a TEST module',
            'namespace': '',
        },
    ]
    assert changelog['releases']['2.10']['plugins'] == {
        'lookup': [
            {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
            },
        ],
    }

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''======================================
Ansible Base 2.10 "meow" Release Notes
======================================

.. contents:: Topics


v2.10
=====

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.

  We have multiple paragraphs in this fragment.

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Update plugin descriptions for 2.10.1 beta 1
    ansible_changelog.set_plugin_cache('2.10.1b1', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '2.10',
            },
            'test_new': {
                'name': 'test_new',
                'description': 'This is ANOTHER test module',
                'namespace': '',
                'version_added': '2.10',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '2.10',
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
                'version_added': '2.9',
            },
        },
    })

    ansible_changelog.add_fragment_line(
        '2.10.1b1.yml', 'release_summary', 'Beta of 2.10.1.')

    # Release 2.10.1b1
    assert ansible_changelog.run_tool('release', [
        '-v',
        '--date', '2020-02-14',
        '--version', '2.10.1b1',
        '--codename', 'woof'
    ]) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['2.10', '2.10.1b1']
    assert changelog['releases']['2.10.1b1']['release_date'] == '2020-02-14'
    assert changelog['releases']['2.10.1b1']['changes'] == {
        'release_summary': 'Beta of 2.10.1.',
        'minor_changes': [
            'Another new fragment.',
        ],
    }
    assert changelog['releases']['2.10.1b1']['fragments'] == [
        '2.10.1b1.yml',
        'test-new-fragment.yml',
    ]
    assert changelog['releases']['2.10.1b1']['modules'] == [
        {
            'name': 'test_new',
            'description': 'This is ANOTHER test module',
            'namespace': '',
        },
    ]
    assert 'plugins' not in changelog['releases']['2.10.1b1']
    assert changelog['releases']['2.10.1b1']['codename'] == 'woof'

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''======================================
Ansible Base 2.10 "woof" Release Notes
======================================

.. contents:: Topics


v2.10.1b1
=========

Release Summary
---------------

Beta of 2.10.1.

Minor Changes
-------------

- Another new fragment.

New Modules
-----------

- test_new - This is ANOTHER test module

v2.10
=====

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.

  We have multiple paragraphs in this fragment.

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Update plugin descriptions for 2.10.1
    ansible_changelog.set_plugin_cache('2.10.1', {
        'module': {
            'test': {
                'name': 'test',
                'description': 'This is a TEST module',
                'namespace': '',
                'version_added': '2.10',
            },
            'test_new': {
                'name': 'test_new',
                'description': 'This is ANOTHER test module',
                'namespace': '',
                'version_added': '2.10',
            },
            'test_new2': {
                'name': 'test_new2',
                'description': 'This is ANOTHER test module!!!11',
                'namespace': '',
                'version_added': '2.10',
            },
            'test_new3': {
                'name': 'test_new3',
                'description': 'This is yet another test module.',
                'namespace': '',
                'version_added': '2.10.1',
            },
        },
        'lookup': {
            'bar': {
                'name': 'bar',
                'description': 'A foo_bar lookup',
                'namespace': None,
                'version_added': '2.10',
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
                'version_added': '2.9',
            },
        },
    })

    ansible_changelog.add_fragment_line(
        '2.10.1.yml', 'release_summary', 'Final release of 2.10.1.')
    ansible_changelog.add_fragment_line(
        'minorchange.yml', 'minor_changes', ['A minor change.'])
    ansible_changelog.add_fragment_line(
        'bugfix.yml', 'bugfixes', ['A bugfix.'])

    # Final release 2.10.1
    assert ansible_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-02-29',
        '--version', '2.10.1',
        '--codename', 'woof!'
    ]) == 0

    diff = ansible_changelog.diff()
    assert diff.added_dirs == []
    assert diff.added_files == []
    assert diff.removed_dirs == []
    assert diff.removed_files == []
    assert diff.changed_files == ['changelogs/CHANGELOG-v2.10.rst', 'changelogs/changelog.yaml']

    changelog = diff.parse_yaml('changelogs/changelog.yaml')
    assert changelog['ancestor'] is None
    assert list(changelog['releases']) == ['2.10', '2.10.1', '2.10.1b1']
    assert changelog['releases']['2.10.1']['release_date'] == '2020-02-29'
    assert changelog['releases']['2.10.1']['changes'] == {
        'release_summary': 'Final release of 2.10.1.',
        'bugfixes': ['A bugfix.'],
        'minor_changes': ['A minor change.'],
    }
    assert changelog['releases']['2.10.1']['fragments'] == [
        '2.10.1.yml',
        'bugfix.yml',
        'minorchange.yml',
    ]
    assert changelog['releases']['2.10.1']['modules'] == [
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
    assert 'plugins' not in changelog['releases']['2.10.1']
    assert changelog['releases']['2.10.1']['codename'] == 'woof!'

    assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
        r'''=======================================
Ansible Base 2.10 "woof!" Release Notes
=======================================

.. contents:: Topics


v2.10.1
=======

Release Summary
---------------

Final release of 2.10.1.

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

v2.10
=====

Release Summary
---------------

This is the first proper release.

Minor Changes
-------------

- baz lookup - no longer ignores the ``bar`` option.

  We have multiple paragraphs in this fragment.

New Plugins
-----------

Lookup
~~~~~~

- bar - A foo_bar lookup

New Modules
-----------

- test - This is a TEST module
''')

    # Final release 2.10.1 again - should not change
    assert ansible_changelog.run_tool('release', [
        '-vvv',
        '--date', '2020-03-01',
        '--version', '2.10.1',
        '--codename', 'woof!!!'
    ]) == 0

    assert ansible_changelog.diff().unchanged

    # Lint fragments
    assert ansible_changelog.run_tool('lint', ['-vv']) == 0


FAKE_PLUGINS = {
    'callback': {
        'test_callback': {
            'doc': {
                'author': ['Someone else'],
                'description': ['This is a relatively new callback added before.'],
                'filename': os.path.join('lib', 'ansible', 'plugins', 'callback', 'test_callback.py'),
                'name': 'test_callback',
                'options': {},
                'short_description': 'A not so old callback',
                'version_added': '2.9',
            },
            'examples': '# Some examples\n',
            'metadata': {
                'status': ['preview'],
                'supported_by': 'community',
            },
            'return': {},
        }
    },
    'module': {
        'old_module': {
            'doc': {
                'author': ['Elder'],
                'description': ['This is an old module.'],
                'filename': os.path.join('lib', 'ansible', 'modules', 'cloud', 'sky', 'old_module.py'),
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
        'test_module': {
            'doc': {
                'author': ['Someone'],
                'description': ['This is a test module.'],
                'filename': os.path.join('lib', 'ansible', 'modules', 'test_module.py'),
                'name': 'test_module',
                'options': {},
                'short_description': 'A test module',
                'version_added': '2.10',
            },
            'examples': '',
            'metadata': {
                'status': ['preview'],
                'supported_by': 'community',
            },
            'return': {},
        }
    },
}


def test_changelog_release_ansible_plugin_cache(  # pylint: disable=redefined-outer-name
        ansible_changelog):  # noqa: F811
    with mock.patch('subprocess.check_output',
                    ansible_changelog.create_fake_subprocess_ansible_doc(FAKE_PLUGINS)):
        ansible_config_contents = r'''
---
title: Ansible Base
release_tag_re: '(v(?:[\d.ab\-]|rc)+)'
pre_release_tag_re: '(?P<pre_release>(?:[ab]|rc)+\d*)$'
changes_file: changelog.yaml
changes_format: combined
keep_fragments: true
always_refresh: true
mention_ancestor: false
notesdir: fragments
prelude_section_name: release_summary
new_plugins_after_name: removed_features
sections:
- ['major_changes', 'Major Changes']
- ['minor_changes', 'Minor Changes']
- ['deprecated_features', 'Deprecated Features']
- ['removed_features', 'Removed Features (previously deprecated)']
- ['bugfixes', 'Bugfixes']
- ['known_issues', 'Known Issues']
'''
        ansible_changelog.set_config_raw(ansible_config_contents.encode('utf-8'))
        ansible_changelog.set_plugin_cache('2.9', {
            'lookup': {
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
                    'version_added': '2.9',
                },
            },
        })
        ansible_changelog.add_fragment_line(
            '2.10.yml', 'release_summary', 'This is the first proper release.')
        ansible_changelog.add_plugin('module', 'test_module.py', create_plugin(
            DOCUMENTATION={
                'name': 'test_module',
                'short_description': 'A test module',
                'version_added': '2.10',
                'description': ['This is a test module.'],
                'author': ['Someone'],
                'options': {},
            },
            EXAMPLES='',
            RETURN={},
        ))
        ansible_changelog.add_plugin('module', '__init__.py', create_plugin(
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
        ansible_changelog.add_plugin('module', 'old_module.py', create_plugin(
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
        ansible_changelog.add_plugin('module', 'bad_module2', create_plugin(
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
        ansible_changelog.add_plugin('callback', 'test_callback.py', create_plugin(
            DOCUMENTATION={
                'name': 'test_callback',
                'short_description': 'A not so old callback',
                'version_added': '2.9',
                'description': ['This is a relatively new callback added before.'],
                'author': ['Someone else'],
                'options': {},
            },
            EXAMPLES='# Some examples\n',
            RETURN={},
        ))
        ansible_changelog.add_plugin('callback', 'test_callback2.py', create_plugin(
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

        assert ansible_changelog.run_tool('release', [
            '-v',
            '--date', '2020-01-02',
            '--version', '2.10',
            '--codename', 'meow'
        ]) == 0

        diff = ansible_changelog.diff()
        assert diff.added_dirs == []
        assert diff.added_files == [
            'changelogs/CHANGELOG-v2.10.rst',
            'changelogs/changelog.yaml',
        ]
        assert diff.removed_dirs == []
        assert diff.removed_files == []
        assert diff.changed_files == [
            'changelogs/.plugin-cache.yaml',
        ]

        plugin_cache = diff.parse_yaml('changelogs/.plugin-cache.yaml')
        assert plugin_cache['version'] == '2.10'

        # Plugin cache: modules
        assert sorted(plugin_cache['plugins']['module']) == ['old_module', 'test_module']
        assert plugin_cache['plugins']['module']['old_module']['name'] == 'old_module'
        assert plugin_cache['plugins']['module']['old_module']['namespace'] == 'cloud.sky'
        assert plugin_cache['plugins']['module']['old_module']['description'] == 'An old module'
        assert plugin_cache['plugins']['module']['old_module']['version_added'] is None
        assert plugin_cache['plugins']['module']['test_module']['name'] == 'test_module'
        assert plugin_cache['plugins']['module']['test_module']['namespace'] == ''
        assert plugin_cache['plugins']['module']['test_module']['description'] == 'A test module'
        assert plugin_cache['plugins']['module']['test_module']['version_added'] == '2.10'

        # Plugin cache: callbacks
        assert sorted(plugin_cache['plugins']['callback']) == ['test_callback']
        assert plugin_cache['plugins']['callback']['test_callback']['name'] == 'test_callback'
        assert plugin_cache['plugins']['callback']['test_callback']['description'] == \
            'A not so old callback'
        assert plugin_cache['plugins']['callback']['test_callback']['version_added'] == '2.9'
        assert 'namespace' not in plugin_cache['plugins']['callback']['test_callback']

        # Changelog
        changelog = diff.parse_yaml('changelogs/changelog.yaml')
        assert changelog['ancestor'] is None
        assert sorted(changelog['releases']) == ['2.10']
        assert changelog['releases']['2.10']['release_date'] == '2020-01-02'
        assert changelog['releases']['2.10']['changes'] == {
            'release_summary': 'This is the first proper release.'
        }
        assert changelog['releases']['2.10']['fragments'] == ['2.10.yml']
        assert len(changelog['releases']['2.10']['modules']) == 1
        assert changelog['releases']['2.10']['modules'][0]['name'] == 'test_module'
        assert changelog['releases']['2.10']['modules'][0]['namespace'] == ''
        assert changelog['releases']['2.10']['modules'][0]['description'] == 'A test module'
        assert 'version_added' not in changelog['releases']['2.10']['modules'][0]

        assert diff.file_contents['changelogs/CHANGELOG-v2.10.rst'].decode('utf-8') == (
            r'''======================================
Ansible Base 2.10 "meow" Release Notes
======================================

.. contents:: Topics


v2.10
=====

Release Summary
---------------

This is the first proper release.

New Modules
-----------

- test_module - A test module
''')

        # Force reloading plugins. This time use ansible-doc for listing plugins.
        assert ansible_changelog.run_tool('generate', ['-v', '--reload-plugins', '--use-ansible-doc']) == 0

        diff = ansible_changelog.diff()
        diff.dump()
        assert diff.unchanged

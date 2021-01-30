# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test basic changelog functionality: lint fragments
"""

import os

from typing import List

import mock

from antsibull_changelog.config import PathsConfig

from fixtures import collection_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin


def test_changelog_fragment_lint_correct(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line(
        '1.0.0.yml', 'release_summary', 'This is the first proper release.')
    collection_changelog.add_fragment_line(
        'test-new-option.yml', 'minor_changes', ['test - has a new option ``foo``.'])
    collection_changelog.add_fragment_line(
        'baz-new-option.yaml', 'minor_changes',
        ['baz lookup - no longer ignores the ``bar`` option.'])
    collection_changelog.add_fragment_line(
        'trivial.yaml', 'trivial', ['Something trivial.'])

    # Lint fragments
    rc, stdout, stderr = collection_changelog.run_tool_w_output('lint', [])
    assert rc == 0
    assert stdout == ''

    # Lint explicitly named fragment
    rc, stdout, stderr = collection_changelog.run_tool_w_output('lint', ['changelogs/fragments/1.0.0.yml'])
    assert rc == 0
    assert stdout == ''


def test_changelog_fragment_lint_broken(  # pylint: disable=redefined-outer-name
        collection_changelog):  # noqa: F811
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_fragment_line('list-instead-of-string.yml', 'release_summary', ['List', 'asfd'])
    collection_changelog.add_fragment_line('int-instead-of-string.yml', 'release_summary', 42)
    collection_changelog.add_fragment_line('int-instead-of-list.yml', 'bugfixes', 42)
    collection_changelog.add_fragment_line('string-instead-of-list.yml', 'minor_changes', 'test')
    collection_changelog.add_fragment_line('list-of-ints.yaml', 'minor_changes', [42, 37])
    collection_changelog.add_fragment_line('wrong-category.yaml', 'minor_change', ['a'])
    collection_changelog.add_fragment('not-a-dict.yaml', '23')
    collection_changelog.add_fragment('invalid-yaml.yaml', 'test: {')
    collection_changelog.add_fragment_generic('invalid-add-obj.yaml', {
        'add object.foo': [
        ],
        'add object.role': [
            'bah',
            {
                'meh': 'bar',
            },
        ],
        'add moo.role': [],
        'add plugin.asdf': [],
        'add plugin.test': 'str',
        'add plugin.module': [
            {
                'meh': '',
            },
        ],
    })

    # Lint fragments
    rc, stdout, stderr = collection_changelog.run_tool_w_output('lint', [])
    assert rc == 3
    assert stdout == r'''
changelogs/fragments/int-instead-of-list.yml:0:0: section "bugfixes" must be type list not int
changelogs/fragments/int-instead-of-string.yml:0:0: section "release_summary" must be type str not int
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add moo.role"'s name must be of format "add (object|plugin).(type)"
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add object.foo"'s type must be one of role, playbook, not "foo"
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add object.role" entry #1 has invalid keys "meh"
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add object.role" entry #1 must have a "description" entry of type string
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add object.role" entry #1 must have a "name" entry of type string
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add object.role" list items must be type dict not str
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.asdf"'s type must be one of become, cache, callback, cliconf, connection, httpapi, inventory, lookup, netconf, shell, vars, module, strategy, module, test, filter, not "asdf"
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.module" entry #0 has invalid keys "meh"
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.module" entry #0 must have a "description" entry of type string
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.module" entry #0 must have a "name" entry of type string
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.module" entry #0 must not have a non-null "namespace" entry
changelogs/fragments/invalid-add-obj.yaml:0:0: section "add plugin.test" must be type list not str
changelogs/fragments/invalid-yaml.yaml:0:0: yaml parsing error
changelogs/fragments/list-instead-of-string.yml:0:0: section "release_summary" must be type str not list
changelogs/fragments/list-of-ints.yaml:0:0: section "minor_changes" list items must be type str not int
changelogs/fragments/not-a-dict.yaml:0:0: file must be a mapping not int
changelogs/fragments/string-instead-of-list.yml:0:0: section "minor_changes" must be type list not str
changelogs/fragments/wrong-category.yaml:0:0: invalid section: minor_change
'''.lstrip()

    # Lint non-existing fragment
    rc, stdout, stderr = collection_changelog.run_tool_w_output('lint', ['changelogs/fragments/non-existing'])
    assert rc == 3
    assert stdout == r'''
changelogs/fragments/non-existing:0:0: yaml parsing error
'''.lstrip()

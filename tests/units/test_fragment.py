# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test fragment module.
"""

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.errors import ChangelogError
from antsibull_changelog.fragment import ChangelogFragment, load_fragments


def test_fragment_combine_fail():
    a = ChangelogFragment({
        'minor_changes': ['1']
    }, '')
    b = ChangelogFragment({
        'minor_changes': '2'
    }, '')
    c = ChangelogFragment({
        'minor_changes': ['3']
    }, '')
    with pytest.raises(ChangelogError):
        ChangelogFragment.combine([a, b, c])


def test_fragment_loading_fail(tmp_path):
    paths = PathsConfig.force_ansible(str(tmp_path))
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    p = tmp_path / 'test.yaml'
    p.write_text('test: [')
    with pytest.raises(ChangelogError):
        load_fragments(paths, config, [str(p)])


def test_fragments_filename_ignore(tmp_path):
    '''Ensure we don't load files we mean to ignore'''
    paths = PathsConfig.force_ansible(str(tmp_path))
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    test_filenames = ['.test.yaml', 'test.yaml~', 'test.yml~', 'test', 'valid.yml', 'valid.yaml']

    for fn in test_filenames:
        p = tmp_path / fn
        p.write_text('minor_changes: ["foo"]')

    loaded = load_fragments(paths, config, [], None, tmp_path)
    assert sorted([x.name for x in  loaded]) == ['valid.yaml', 'valid.yml']

    config.ignore_other_fragment_extensions = False
    loaded = load_fragments(paths, config, [], None, tmp_path)
    assert sorted([x.name for x in  loaded]) == ['test', 'test.yaml~', 'test.yml~', 'valid.yaml', 'valid.yml']

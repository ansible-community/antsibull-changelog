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

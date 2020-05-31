# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test changes module.
"""

import datetime
import os

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.changes import ChangesBase, ChangesData, ChangesMetadata


def test_changes_data():
    paths = PathsConfig.force_collection('/')
    details = CollectionDetails(paths)
    config = ChangelogConfig.default(paths, details)

    data = {
        'ancestor': None,
        'releases': {},
    }

    changes = ChangesData(
        config,
        os.path.join(config.paths.changelog_dir, config.changes_file),
        data_override=data)
    changes.ancestor = '0.1.0'

    assert not changes.has_release
    assert sorted(changes.releases.keys()) == []

    changes.add_release('1.1.0', None, datetime.date(2020, 2, 1))

    assert changes.has_release
    assert sorted(changes.releases.keys()) == ['1.1.0']
    assert changes.latest_version == '1.1.0'

    changes.add_release('1.0.0', None, datetime.date(2020, 1, 1))

    assert changes.has_release
    assert sorted(changes.releases.keys()) == ['1.0.0', '1.1.0']
    assert changes.latest_version == '1.1.0'

    changes.add_release('1.2.0', None, datetime.date(2020, 3, 1))

    assert changes.has_release
    assert sorted(changes.releases.keys()) == ['1.0.0', '1.1.0', '1.2.0']
    assert changes.latest_version == '1.2.0'

    changes.add_release('1.2.1', None, datetime.date(2020, 3, 2))
    changes.add_release('1.3.0-alpha', None, datetime.date(2020, 3, 3))
    changes.add_release('1.3.0-beta', None, datetime.date(2020, 3, 4))
    changes.add_release('1.3.0', None, datetime.date(2020, 3, 5))
    changes.add_release('1.3.1-alpha', None, datetime.date(2020, 3, 6))

    assert sorted(changes.releases.keys()) == [
        '1.0.0',
        '1.1.0',
        '1.2.0',
        '1.2.1',
        '1.3.0', '1.3.0-alpha', '1.3.0-beta',
        '1.3.1-alpha',
    ]

    changes2 = ChangesData(
        config,
        os.path.join(config.paths.changelog_dir, config.changes_file),
        data_override=ChangesBase.empty())
    changes2.ancestor = '1.3.1-alpha'
    changes2.add_release('1.3.2', None, datetime.date(2020, 3, 10))
    changes2.add_release('1.3.3', None, datetime.date(2020, 3, 10))
    assert sorted(changes2.releases.keys()) == [
        '1.3.2',
        '1.3.3',
    ]

    changes3 = ChangesData(
        config,
        os.path.join(config.paths.changelog_dir, config.changes_file),
        data_override=ChangesBase.empty())
    changes3.add_release('0.1.0', None, datetime.date(2019, 7, 30))
    changes3.add_release('0.2.0', None, datetime.date(2019, 12, 31))
    assert sorted(changes3.releases.keys()) == [
        '0.1.0',
        '0.2.0',
    ]

    for order in [
        [changes, changes2],
        [changes2, changes],
    ]:
        changes_concat = ChangesData.concatenate(order)
        assert sorted(changes_concat.releases.keys()) == [
            '1.0.0',
            '1.1.0',
            '1.2.0',
            '1.2.1',
            '1.3.0', '1.3.0-alpha', '1.3.0-beta',
            '1.3.1-alpha',
            '1.3.2',
            '1.3.3',
        ]
        assert changes_concat.ancestor == '0.1.0'

    for order in [
        [changes, changes2, changes3],
        [changes, changes3, changes2],
        [changes2, changes, changes3],
        [changes2, changes3, changes],
        [changes3, changes, changes2],
        [changes3, changes2, changes],
    ]:
        changes_concat = ChangesData.concatenate(order)
        assert sorted(changes_concat.releases.keys()) == [
            '0.1.0',
            '0.2.0',
            '1.0.0',
            '1.1.0',
            '1.2.0',
            '1.2.1',
            '1.3.0', '1.3.0-alpha', '1.3.0-beta',
            '1.3.1-alpha',
            '1.3.2',
            '1.3.3',
        ]
        assert changes_concat.ancestor is None

    changes_concat.ancestor = '0.0.1'

    changes_concat.prune_versions(versions_after='0.1.0', versions_until=None)
    assert sorted(changes_concat.releases.keys()) == [
        '0.2.0',
        '1.0.0',
        '1.1.0',
        '1.2.0',
        '1.2.1',
        '1.3.0', '1.3.0-alpha', '1.3.0-beta',
        '1.3.1-alpha',
        '1.3.2',
        '1.3.3',
    ]
    assert changes_concat.ancestor == '0.1.0'

    changes_concat.prune_versions(versions_after=None, versions_until='1.3.2')
    assert sorted(changes_concat.releases.keys()) == [
        '0.2.0',
        '1.0.0',
        '1.1.0',
        '1.2.0',
        '1.2.1',
        '1.3.0', '1.3.0-alpha', '1.3.0-beta',
        '1.3.1-alpha',
        '1.3.2',
    ]
    assert changes_concat.ancestor == '0.1.0'

    changes_concat.prune_versions(versions_after='1.1.0', versions_until='1.3.0')
    assert sorted(changes_concat.releases.keys()) == [
        '1.2.0',
        '1.2.1',
        '1.3.0', '1.3.0-alpha', '1.3.0-beta',
    ]
    assert changes_concat.ancestor == '1.1.0'

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test utils module.
"""

from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.errors import ChangelogError
from antsibull_changelog.utils import detect_vcs, is_release_version


@pytest.mark.parametrize(
    "version, is_release",
    [
        ("2.10", True),
        ("2.10a1", False),
        ("2.10b1", False),
        ("2.10rc1", False),
        ("2.10rc2", False),
        ("2.10.1", True),
        ("2.10.1a1", False),
        ("2.10.1b1", False),
        ("2.10.1rc1", False),
        ("2.10.1rc2", False),
    ],
)
def test_is_release_version_ansible(version, is_release):
    paths = PathsConfig.force_ansible(".")
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    config.release_tag_re = r"(v(?:[\d.ab\-]|rc)+)"
    config.pre_release_tag_re = r"(?P<pre_release>(?:[ab]|rc)+\d*)$"
    assert is_release_version(config, version) == is_release


@pytest.mark.parametrize(
    "version",
    [
        ("A",),
        # ('2c', ), -- this is actually valid...
    ],
)
def test_is_release_version_ansible_fail(version):
    paths = PathsConfig.force_ansible(".")
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    config.release_tag_re = r"(v(?:[\d.ab\-]|rc)+)"
    config.pre_release_tag_re = r"(?P<pre_release>(?:[ab]|rc)+\d*)$"
    with pytest.raises(ChangelogError):
        print(is_release_version(config, version))


@pytest.mark.parametrize(
    "version, is_release",
    [
        ("1.0.0", True),
        ("1.0.0-alpha", False),
        ("1.0.0+test", True),
        ("1.0.0-alpha+test", False),
    ],
)
def test_is_release_version_collection(version, is_release):
    paths = PathsConfig.force_collection(".")
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    assert is_release_version(config, version) == is_release


@pytest.mark.parametrize(
    "version",
    [
        ("1.0.0.0",),
        ("2.10",),
        ("2.10a1",),
        ("2.10.1a1",),
    ],
)
def test_is_release_version_collection_fail(version):
    paths = PathsConfig.force_collection(".")
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    with pytest.raises(ChangelogError):
        is_release_version(config, version)


def test_detect_vcs():
    path = "/path/to/dir"
    git_command = ["git", "-C", path, "rev-parse", "--is-inside-work-tree"]

    with mock.patch(
        "subprocess.check_output",
        return_value="true\n".encode("utf-8"),
    ) as m:
        assert detect_vcs(path) == "git"
        m.assert_called_with(git_command)

    with mock.patch(
        "subprocess.check_output",
        return_value="foobar\n".encode("utf-8"),
    ) as m:
        assert detect_vcs(path) == "none"
        m.assert_called_with(git_command)

    with mock.patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(128, path),
    ) as m:
        assert detect_vcs(path) == "none"
        m.assert_called_with(git_command)

    with mock.patch(
        "subprocess.check_output",
        side_effect=FileNotFoundError(),
    ) as m:
        assert detect_vcs(path) == "none"
        m.assert_called_with(git_command)

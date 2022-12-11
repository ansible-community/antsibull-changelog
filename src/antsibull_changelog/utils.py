# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Utility functions.
"""

from __future__ import annotations

import re

from collections.abc import Callable, Collection
from typing import Any

import packaging.version
import semantic_version

from .config import ChangelogConfig
from .errors import ChangelogError


def get_version_constructor(config: ChangelogConfig) -> Callable[[str], Any]:
    """
    Returns a version object constructor for the given changelog config.

    :arg config: The changelog configuration
    :return: A callable which converts a string to a version object
    """
    if config.use_semantic_versioning:
        return semantic_version.Version
    return packaging.version.Version


def is_release_version(config: ChangelogConfig, version: str) -> bool:
    """
    Determine the type of release from the given version.

    :arg config: The changelog configuration
    :arg version: The version to check
    :return: Whether the provided version is a release version
    """
    if config.use_semantic_versioning:
        try:
            return not bool(semantic_version.Version(version).prerelease)
        except Exception as exc:  # pylint: disable=broad-except
            raise ChangelogError(
                'unsupported semantic version format: %s (%s)' % (version, exc)) from exc

    tag_format = 'v%s' % version

    if re.search(config.pre_release_tag_re, tag_format):
        return False

    if re.search(config.release_tag_re, tag_format):
        return True

    raise ChangelogError('unsupported version format: %s' % version)


def collect_versions(versions: Collection[str],
                     config: ChangelogConfig,
                     after_version: str | None = None,
                     until_version: str | None = None,
                     squash: bool = False) -> list[tuple[str, list[str]]]:
    """
    Collect all versions of interest and return them as an ordered list,
    latest to earliest. The versions are grouped by versions that should
    result in a changelog entry.
    """
    version_constructor = get_version_constructor(config)
    result: list[tuple[str, list[str]]] = []
    entry: tuple[str, list[str]] | None = None
    for version in sorted(versions, reverse=True, key=version_constructor):
        if after_version is not None:
            if version_constructor(version) <= version_constructor(after_version):
                continue
        if until_version is not None:
            if version_constructor(version) > version_constructor(until_version):
                continue

        version_list: list[str]
        if not squash and is_release_version(config, version):
            # next version is a release, it needs its own entry
            version_list = []
            entry = (version, version_list)
            result.append(entry)
        elif entry is None:
            version_list = []
            entry = (version, version_list)
            result.append(entry)
        elif not squash and not is_release_version(config, entry[0]): \
                # pylint: disable=unsubscriptable-object
            # current version is a pre-release, next version needs its own entry
            version_list = []
            entry = (version, version_list)
            result.append(entry)
        else:
            version_list = entry[1]  # pylint: disable=unsubscriptable-object

        version_list.append(version)

    return result

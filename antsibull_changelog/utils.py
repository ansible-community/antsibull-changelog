# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Utility functions.
"""

import re

import semantic_version

from .config import ChangelogConfig
from .errors import ChangelogError


def is_release_version(config: ChangelogConfig, version: str) -> bool:
    """
    Determine the type of release from the given version.

    :arg config: The changelog configuration
    :arg version: The version to check
    :return: Whether the provided version is a release version
    """
    if config.is_collection:
        try:
            return not bool(semantic_version.Version(version).prerelease)
        except Exception as exc:  # pylint: disable=broad-except
            raise ChangelogError('unsupported semantic version format: %s (%s)' % (version, exc))

    tag_format = 'v%s' % version

    if re.search(config.pre_release_tag_re, tag_format):
        return False

    if re.search(config.release_tag_re, tag_format):
        return True

    raise ChangelogError('unsupported version format: %s' % version)

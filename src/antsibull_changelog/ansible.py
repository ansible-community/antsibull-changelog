# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Return Ansible-specific information, like current release or list of documentable plugins.
"""

from __future__ import annotations

from functools import cache

import packaging.version

OBJECT_TYPES = ("role", "playbook")

OTHER_PLUGIN_TYPES = ("module", "test", "filter")

# These are pairs (plugin_type, plugin_filename) inside ansible-core which are *not*
# plugins, but files used by plugins.
PLUGIN_EXCEPTIONS = (("cache", "base.py"), ("module", "async_wrapper.py"))


@cache
def get_documentable_plugins() -> tuple[str, ...]:
    """
    Retrieve plugin types that can be documented.
    """
    try:
        # We import from ansible locally since importing it is rather slow
        from ansible import constants as C  # pylint: disable=import-outside-toplevel

        return C.DOCUMENTABLE_PLUGINS
    except ImportError:
        return (
            "become",
            "cache",
            "callback",
            "cliconf",
            "connection",
            "httpapi",
            "inventory",
            "lookup",
            "netconf",
            "shell",
            "vars",
            "module",
            "strategy",
        )


@cache
def get_documentable_objects() -> tuple[str, ...]:
    """
    Retrieve object types that can be documented.
    """
    try:
        # We import from ansible locally since importing it is rather slow
        # pylint: disable-next=import-outside-toplevel
        from ansible import release as ansible_release

        if packaging.version.Version(
            ansible_release.__version__
        ) < packaging.version.Version("2.11.0"):
            return ()
        return ("role",)
    except ImportError:
        return ()


@cache
def get_ansible_release() -> tuple[str, str]:
    """
    Retrieve current version and codename of Ansible.

    :return: Tuple with version and codename
    """
    try:
        # We import from ansible locally since importing it is rather slow
        # pylint: disable-next=import-outside-toplevel
        from ansible import release as ansible_release

        return ansible_release.__version__, ansible_release.__codename__
    except ImportError:
        # pylint: disable-next=raise-missing-from
        raise ValueError("Cannot import ansible.release")

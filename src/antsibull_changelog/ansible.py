# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Return Ansible-specific information, like current release or list of documentable plugins.
"""

from typing import Any, Tuple

import packaging.version

try:
    from ansible import constants as C
    HAS_ANSIBLE_CONSTANTS = True
except ImportError:
    HAS_ANSIBLE_CONSTANTS = False


ansible_release: Any
try:
    from ansible import release as ansible_release
    HAS_ANSIBLE_RELEASE = True
except ImportError:
    ansible_release = None
    HAS_ANSIBLE_RELEASE = False


OBJECT_TYPES = ('role', 'playbook')

OTHER_PLUGIN_TYPES = ('module', 'test', 'filter')

# These are pairs (plugin_type, plugin_filename) inside ansible-core which are *not*
# plugins, but files used by plugins.
PLUGIN_EXCEPTIONS = (('cache', 'base.py'), ('module', 'async_wrapper.py'))


def get_documentable_plugins() -> Tuple[str, ...]:
    """
    Retrieve plugin types that can be documented. Does not include 'module'.
    """
    if HAS_ANSIBLE_CONSTANTS:
        return C.DOCUMENTABLE_PLUGINS
    return (
        'become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory',
        'lookup', 'netconf', 'shell', 'vars', 'module', 'strategy',
    )


def get_documentable_objects() -> Tuple[str, ...]:
    """
    Retrieve object types that can be documented.
    """
    if not HAS_ANSIBLE_RELEASE:
        return ()
    if packaging.version.Version(ansible_release.__version__) < packaging.version.Version('2.11.0'):
        return ()
    return ('role', )


def get_ansible_release() -> Tuple[str, str]:
    """
    Retrieve current version and codename of Ansible.

    :return: Tuple with version and codename
    """
    if not HAS_ANSIBLE_RELEASE:
        raise ValueError('Cannot import ansible.release')
    return ansible_release.__version__, ansible_release.__codename__

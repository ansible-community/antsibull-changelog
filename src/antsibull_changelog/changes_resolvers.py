# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Fragment, plugin and object resolvers.
"""

from __future__ import annotations

import abc
from typing import Any

from .fragment import ChangelogFragment
from .plugins import PluginDescription


class FragmentResolver(metaclass=abc.ABCMeta):
    # pylint: disable=too-few-public-methods
    """
    Allows to resolve a release section to a list of changelog fragments.
    """

    @abc.abstractmethod
    def resolve(self, release: dict) -> list[ChangelogFragment]:
        """
        Return a list of ``ChangelogFragment`` objects from the given release object.

        :arg release: A release description
        :return: A list of changelog fragments
        """


class PluginResolver(metaclass=abc.ABCMeta):
    """
    Allows to resolve a release section to a plugin description database.
    """

    @staticmethod
    def resolve_plugin(plugin: PluginDescription) -> dict[str, Any]:
        """
        Convert a ``PluginDecscription`` object to a plugin description dictionary.
        """
        return {
            "name": plugin.name,
            "namespace": plugin.namespace,
            "description": plugin.description,
        }

    @abc.abstractmethod
    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """


class ChangesDataFragmentResolver(FragmentResolver):
    # pylint: disable=too-few-public-methods
    """
    A ``FragmentResolver`` class for modern ``ChangesData`` objects.
    """

    def resolve(self, release: dict) -> list[ChangelogFragment]:
        """
        Return a list of ``ChangelogFragment`` objects from the given release object.

        :arg release: A release description
        :return: A list of changelog fragments
        """
        changes = release.get("changes")
        if changes is None:
            return []
        return [ChangelogFragment.from_dict(changes)]


class ChangesDataPluginResolver(PluginResolver):
    """
    A ``PluginResolver`` class for modern ``ChangesData`` objects.
    """

    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """
        result = {}
        if "modules" in release:
            result["module"] = release["modules"]
        if "plugins" in release:
            result.update(release["plugins"])
        return result


class ChangesDataObjectResolver(PluginResolver):
    """
    A ``PluginResolver`` class for modern ``ChangesData`` objects.
    """

    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of object types mapping to lists of object descriptions
        for the given release.

        :arg release: A release description
        :return: A map of object types to lists of object descriptions
        """
        result = {}
        if "objects" in release:
            result.update(release["objects"])
        return result

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
    # pylint: disable=too-few-public-methods
    """
    Allows to resolve a release section to a plugin description database.
    """

    @abc.abstractmethod
    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """


class LegacyFragmentResolver(FragmentResolver):
    # pylint: disable=too-few-public-methods
    """
    Given a list of changelog fragments, allows to resolve from a list of fragment names.
    """

    fragments: dict[str, ChangelogFragment]

    def __init__(self, fragments: list[ChangelogFragment]):
        """
        Create a simple fragment resolver.
        """
        self.fragments = {}
        for fragment in fragments:
            self.fragments[fragment.name] = fragment

    def resolve(self, release: dict) -> list[ChangelogFragment]:
        """
        Return a list of ``ChangelogFragment`` objects from the given release object.

        :arg release: A release description
        :return: A list of changelog fragments
        """
        fragment_names: list[str] = release.get('fragments', [])
        return [self.fragments[fragment] for fragment in fragment_names]


class LegacyPluginResolver(PluginResolver):
    # pylint: disable=too-few-public-methods
    """
    Provides a plugin resolved based on a list of ``PluginDescription`` objects.
    """

    plugins: dict[str, dict[str, dict[str, Any]]]

    @staticmethod
    def resolve_plugin(plugin: PluginDescription) -> dict[str, Any]:
        """
        Convert a ``PluginDecscription`` object to a plugin description dictionary.
        """
        return {
            'name': plugin.name,
            'namespace': plugin.namespace,
            'description': plugin.description,
        }

    def __init__(self, plugins: list[PluginDescription]):
        """
        Create a simple plugin resolver from a list of ``PluginDescription`` objects.
        """
        self.plugins = {}
        for plugin in plugins:
            if plugin.type not in self.plugins:
                self.plugins[plugin.type] = {}

            self.plugins[plugin.type][plugin.name] = self.resolve_plugin(plugin)

    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """
        result = {}
        if 'modules' in release:
            result['module'] = [self.plugins['module'][module_name]
                                for module_name in release['modules']]
        if 'plugins' in release:
            for plugin_type, plugin_names in release['plugins'].items():
                result[plugin_type] = [self.plugins[plugin_type][plugin_name]
                                       for plugin_name in plugin_names]
        return result


class LegacyObjectResolver(PluginResolver):
    # pylint: disable=too-few-public-methods
    """
    Provides a object resolved based on a list of ``PluginDescription`` objects.
    """

    def resolve(self, release: dict) -> dict[str, list[dict[str, Any]]]:
        """
        Return a dictionary of object types mapping to lists of object descriptions
        for the given release.

        :arg release: A release description
        :return: A map of object types to lists of plugin descriptions
        """
        return {}


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
        changes = release.get('changes')
        if changes is None:
            return []
        return [ChangelogFragment.from_dict(changes)]


class ChangesDataPluginResolver(PluginResolver):
    # pylint: disable=too-few-public-methods
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
        if 'modules' in release:
            result['module'] = release['modules']
        if 'plugins' in release:
            result.update(release['plugins'])
        return result


class ChangesDataObjectResolver(PluginResolver):
    # pylint: disable=too-few-public-methods
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
        if 'objects' in release:
            result.update(release['objects'])
        return result

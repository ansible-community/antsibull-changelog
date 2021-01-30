# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Fragment, plugin and object resolvers.
"""

import abc

from typing import Any, Dict, List

from .fragment import ChangelogFragment
from .plugins import PluginDescription


class FragmentResolver(metaclass=abc.ABCMeta):
    # pylint: disable=too-few-public-methods
    """
    Allows to resolve a release section to a list of changelog fragments.
    """

    @abc.abstractmethod
    def resolve(self, release: dict) -> List[ChangelogFragment]:
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
    def resolve(self, release: dict) -> Dict[str, List[Dict[str, Any]]]:
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

    fragments: Dict[str, ChangelogFragment]

    def __init__(self, fragments: List[ChangelogFragment]):
        """
        Create a simple fragment resolver.
        """
        self.fragments = dict()
        for fragment in fragments:
            self.fragments[fragment.name] = fragment

    def resolve(self, release: dict) -> List[ChangelogFragment]:
        """
        Return a list of ``ChangelogFragment`` objects from the given release object.

        :arg release: A release description
        :return: A list of changelog fragments
        """
        fragment_names: List[str] = release.get('fragments', [])
        return [self.fragments[fragment] for fragment in fragment_names]


class LegacyPluginResolver(PluginResolver):
    # pylint: disable=too-few-public-methods
    """
    Provides a plugin resolved based on a list of ``PluginDescription`` objects.
    """

    plugins: Dict[str, Dict[str, Dict[str, Any]]]

    @staticmethod
    def resolve_plugin(plugin: PluginDescription) -> Dict[str, Any]:
        """
        Convert a ``PluginDecscription`` object to a plugin description dictionary.
        """
        return dict(
            name=plugin.name,
            namespace=plugin.namespace,
            description=plugin.description,
        )

    def __init__(self, plugins: List[PluginDescription]):
        """
        Create a simple plugin resolver from a list of ``PluginDescription`` objects.
        """
        self.plugins = dict()
        for plugin in plugins:
            if plugin.type not in self.plugins:
                self.plugins[plugin.type] = dict()

            self.plugins[plugin.type][plugin.name] = self.resolve_plugin(plugin)

    def resolve(self, release: dict) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """
        result = dict()
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

    def resolve(self, release: dict) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return a dictionary of object types mapping to lists of object descriptions
        for the given release.

        :arg release: A release description
        :return: A map of object types to lists of plugin descriptions
        """
        return dict()


class ChangesDataFragmentResolver(FragmentResolver):
    # pylint: disable=too-few-public-methods
    """
    A ``FragmentResolver`` class for modern ``ChangesData`` objects.
    """

    def resolve(self, release: dict) -> List[ChangelogFragment]:
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

    def resolve(self, release: dict) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return a dictionary of plugin types mapping to lists of plugin descriptions
        for the given release.

        :arg release: A release description
        :return: A map of plugin types to lists of plugin descriptions
        """
        result = dict()
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

    def resolve(self, release: dict) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return a dictionary of object types mapping to lists of object descriptions
        for the given release.

        :arg release: A release description
        :return: A map of object types to lists of object descriptions
        """
        result = dict()
        if 'objects' in release:
            result.update(release['objects'])
        return result

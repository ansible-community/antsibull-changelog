# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Classes handling ``changelog.yaml`` (new Ansible and collections)
and ``.changes.yaml`` (old Ansible) files.
"""

import abc
import collections
import datetime
import os

from typing import Any, Dict, List, Optional, Set, cast

import packaging.version
import semantic_version

from .config import ChangelogConfig
from .fragment import ChangelogFragment, load_fragments
from .logger import LOGGER
from .plugins import PluginDescription, load_plugins
from .utils import is_release_version
from .yaml import load_yaml, store_yaml


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


class ChangesBase(metaclass=abc.ABCMeta):
    """
    Read, write and manage change metadata.
    """

    config: ChangelogConfig
    path: str
    data: dict
    known_plugins: Set[str]
    known_fragments: Set[str]
    ancestor: Optional[str]

    def __init__(self, config: ChangelogConfig, path: str):
        self.config = config
        self.path = path
        self.data = self.empty()
        self.known_fragments = set()
        self.known_plugins = set()
        self.ancestor = None

    def version_constructor(self, version: str) -> Any:
        """
        Create a version object.
        """
        if self.config.is_collection:
            return semantic_version.Version(version)
        return packaging.version.Version(version)

    @staticmethod
    def empty() -> dict:
        """
        Empty change metadata.
        """
        return dict(
            ancestor=None,
            releases=dict(
            ),
        )

    @property
    def latest_version(self) -> str:
        """
        Latest version in the changes.

        Must only be called if ``has_release`` is ``True``.
        """
        return sorted(self.releases, reverse=True, key=self.version_constructor)[0]

    @property
    def has_release(self) -> bool:
        """
        Whether there is at least one release.
        """
        return bool(self.releases)

    @property
    def releases(self) -> Dict[str, Dict[str, Any]]:
        """
        Dictionary of releases.
        """
        return cast(Dict[str, Dict[str, Any]], self.data['releases'])

    def load(self, data_override: Optional[dict] = None) -> None:
        """
        Load the change metadata from disk.

        :arg data_override: If provided, will use this as loaded data instead of reading self.path
        """
        if data_override is not None:
            self.data = data_override
        elif os.path.exists(self.path):
            self.data = load_yaml(self.path)
        else:
            self.data = self.empty()
        self.ancestor = self.data.get('ancestor')

    @abc.abstractmethod
    def update_plugins(self, plugins: List[PluginDescription]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """

    @abc.abstractmethod
    def update_fragments(self, fragments: List[ChangelogFragment]) -> None:
        """
        Update fragment contents, and remove fragment contents which are not in the provided
        list of fragments.
        """

    @abc.abstractmethod
    def sort(self) -> None:
        """
        Sort change metadata in place.
        """

    def save(self) -> None:
        """
        Save the change metadata to disk.
        """
        self.sort()
        self.data['ancestor'] = self.ancestor
        store_yaml(self.path, self.data)

    def add_release(self, version: str, codename: Optional[str], release_date: datetime.date):
        """
        Add a new releases to the changes metadata.
        """
        if version not in self.releases:
            self.releases[version] = dict(
                release_date=release_date.isoformat(),
            )
            if codename is not None:
                self.releases[version]['codename'] = codename
        else:
            LOGGER.warning('release {} already exists', version)

    @abc.abstractmethod
    def add_fragment(self, fragment: ChangelogFragment, version: str):
        """
        Add a new changelog fragment to the change metadata for the given version.
        """

    @staticmethod
    def _create_plugin_entry(plugin: PluginDescription) -> Any:
        return plugin.name

    def add_plugin(self, plugin: PluginDescription, version: str):
        """
        Add a new plugin to the change metadata for the given version.

        If the plugin happens to be already known (for another version),
        it will not be added.

        :return: ``True`` if the plugin was added for this version
        """
        composite_name = '%s/%s' % (plugin.type, plugin.name)

        if composite_name in self.known_plugins:
            return False

        self.known_plugins.add(composite_name)

        if plugin.type == 'module':
            if 'modules' not in self.releases[version]:
                self.releases[version]['modules'] = []

            modules = self.releases[version]['modules']
            modules.append(self._create_plugin_entry(plugin))
        else:
            if 'plugins' not in self.releases[version]:
                self.releases[version]['plugins'] = {}

            plugins = self.releases[version]['plugins']

            if plugin.type not in plugins:
                plugins[plugin.type] = []

            plugins[plugin.type].append(self._create_plugin_entry(plugin))

        return True

    @abc.abstractmethod
    def get_plugin_resolver(
            self, plugins: Optional[List[PluginDescription]] = None) -> PluginResolver:
        """
        Create a plugin resolver.

        If the plugins are not provided and needed by this object, they might be loaded.
        """

    @abc.abstractmethod
    def get_fragment_resolver(
            self, fragments: Optional[List[ChangelogFragment]] = None) -> FragmentResolver:
        """
        Create a fragment resolver.

        If the fragments are not provided and needed by this object, they might be loaded.
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


class ChangesMetadata(ChangesBase):
    """
    Read, write and manage classic Ansible (2.9 and earlier) change metadata.
    """

    def __init__(self, config: ChangelogConfig, path: str):
        """
        Create legacy change metadata.
        """
        super(ChangesMetadata, self).__init__(config, path)
        self.load()

    def load(self, data_override: Optional[dict] = None) -> None:
        """
        Load the change metadata from disk.
        """
        super(ChangesMetadata, self).load(data_override=data_override)

        for _, config in self.releases.items():
            for plugin_type, plugin_names in config.get('plugins', {}).items():
                self.known_plugins |= set(
                    '%s/%s' % (plugin_type, plugin_name) for plugin_name in plugin_names)

            module_names = config.get('modules', [])

            self.known_plugins |= set('module/%s' % module_name for module_name in module_names)

            self.known_fragments |= set(config.get('fragments', []))

    def update_plugins(self, plugins: List[PluginDescription]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """
        valid_plugins = collections.defaultdict(set)

        for plugin in plugins:
            valid_plugins[plugin.type].add(plugin.name)

        for _, config in self.releases.items():
            if 'modules' in config:
                invalid_modules = set(
                    module for module in config['modules']
                    if module not in valid_plugins['module'])
                config['modules'] = [
                    module for module in config['modules']
                    if module not in invalid_modules]
                self.known_plugins -= set(
                    'module/%s' % module for module in invalid_modules)

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    invalid_plugins = set(
                        plugin for plugin in config['plugins'][plugin_type]
                        if plugin not in valid_plugins[plugin_type])
                    config['plugins'][plugin_type] = [
                        plugin for plugin in config['plugins'][plugin_type]
                        if plugin not in invalid_plugins]
                    self.known_plugins -= set(
                        '%s/%s' % (plugin_type, plugin) for plugin in invalid_plugins)

    def update_fragments(self, fragments: List[ChangelogFragment]) -> None:
        """
        Update fragment contents, and remove fragment contents which are not in the provided
        list of fragments.
        """
        valid_fragments = set(fragment.name for fragment in fragments)

        for _, config in self.releases.items():
            if 'fragments' not in config:
                continue

            invalid_fragments = set(
                fragment for fragment in config['fragments']
                if fragment not in valid_fragments)
            config['fragments'] = [
                fragment for fragment in config['fragments']
                if fragment not in invalid_fragments]
            self.known_fragments -= invalid_fragments

    def sort(self) -> None:
        """
        Sort change metadata in place.
        """
        for _, config in self.data['releases'].items():
            if 'modules' in config:
                config['modules'] = sorted(config['modules'])

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    config['plugins'][plugin_type] = sorted(config['plugins'][plugin_type])

            if 'fragments' in config:
                config['fragments'] = sorted(config['fragments'])

    def add_fragment(self, fragment: ChangelogFragment, version: str) -> bool:
        """
        Add a changelog fragment to the change metadata.
        """
        if fragment.name in self.known_fragments:
            return False

        self.known_fragments.add(fragment.name)

        if 'fragments' not in self.releases[version]:
            self.releases[version]['fragments'] = []

        fragments = self.releases[version]['fragments']
        fragments.append(fragment.name)
        return True

    def get_plugin_resolver(
            self, plugins: Optional[List[PluginDescription]] = None) -> PluginResolver:
        """
        Create a plugin resolver.

        If the plugins are not provided and needed by this object, they **will** be loaded.
        """
        if plugins is None:
            plugins = load_plugins(paths=self.config.paths,
                                   collection_details=self.config.collection_details,
                                   version=self.latest_version,
                                   force_reload=False)
        return LegacyPluginResolver(plugins)

    def get_fragment_resolver(
            self, fragments: Optional[List[ChangelogFragment]] = None) -> FragmentResolver:
        """
        Create a fragment resolver.

        If the fragments are not provided and needed by this object, they **will** be loaded.
        """
        if fragments is None:
            fragments = load_fragments(paths=self.config.paths, config=self.config)
        return LegacyFragmentResolver(fragments)


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


class ChangesData(ChangesBase):
    """
    Read, write and manage modern change metadata.

    This is the format used for ansible-base 2.10+ and for Ansible collections.
    """

    config: ChangelogConfig

    def __init__(self, config: ChangelogConfig, path: str, data_override: Optional[dict] = None):
        """
        Create modern change metadata.

        :arg data_override: Allows to load data from dictionary instead from disk
        """
        super(ChangesData, self).__init__(config, path)
        self.config = config
        self.load(data_override=data_override)

    def load(self, data_override: Optional[dict] = None) -> None:
        """
        Load the change metadata from disk.
        """
        super(ChangesData, self).load(data_override=data_override)

        for _, config in self.releases.items():
            for plugin_type, plugins in config.get('plugins', {}).items():
                self.known_plugins |= set(
                    '%s/%s' % (plugin_type, plugin['name']) for plugin in plugins)

            modules = config.get('modules', [])

            self.known_plugins |= set('module/%s' % module['name'] for module in modules)

            self.known_fragments |= set(config.get('fragments', []))

    def update_plugins(self, plugins: List[PluginDescription]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """
        valid_plugins: Dict[str, Dict[str, PluginDescription]] = collections.defaultdict(dict)

        for plugin in plugins:
            valid_plugins[plugin.type][plugin.name] = plugin

        for _, config in self.releases.items():
            if 'modules' in config:
                invalid_module_names = set(
                    module['name'] for module in config['modules']
                    if module['name'] not in valid_plugins['module'])
                config['modules'] = [
                    self._create_plugin_entry(valid_plugins['module'][module['name']])
                    for module in config['modules']
                    if module['name'] not in invalid_module_names]
                self.known_plugins -= set(
                    'module/%s' % module_name for module_name in invalid_module_names)

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    invalid_plugin_names = set(
                        plugin['name'] for plugin in config['plugins'][plugin_type]
                        if plugin['name'] not in valid_plugins[plugin_type])
                    config['plugins'][plugin_type] = [
                        self._create_plugin_entry(valid_plugins[plugin_type][plugin['name']])
                        for plugin in config['plugins'][plugin_type]
                        if plugin['name'] not in invalid_plugin_names]
                    self.known_plugins -= set(
                        '%s/%s' % (plugin_type, plugin_name)
                        for plugin_name in invalid_plugin_names)

    def update_fragments(self, fragments: List[ChangelogFragment]) -> None:
        """
        Update fragment contents, and remove fragment contents which are not in the provided
        list of fragments.

        Must only be called if ``keep_fragments`` is set to ``True`` in the configuration.
        """
        assert self.config.keep_fragments
        valid_fragments = {fragment.name: fragment for fragment in fragments}
        for _, config in self.releases.items():
            config.pop('changes', None)

            if 'fragments' in config:
                invalid_fragments = set(
                    fragment for fragment in config['fragments']
                    if fragment not in valid_fragments)
                config['fragments'] = [
                    fragment for fragment in config['fragments']
                    if fragment not in invalid_fragments]
                self.known_fragments -= invalid_fragments

                config['changes'] = ChangelogFragment.combine([
                    valid_fragments[fragment] for fragment in config['fragments']])

    def sort(self) -> None:
        """
        Sort change metadata in place.
        """
        super(ChangesData, self).sort()

        for _, config in self.data['releases'].items():
            if 'modules' in config:
                config['modules'] = sorted(config['modules'], key=lambda module: module['name'])

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    config['plugins'][plugin_type] = sorted(
                        config['plugins'][plugin_type], key=lambda plugin: plugin['name'])

            if 'fragments' in config:
                config['fragments'] = sorted(config['fragments'])

            if 'changes' in config:
                config['changes'] = {
                    section: sorted(entries) if section != self.config.prelude_name else entries
                    for section, entries in sorted(config['changes'].items())
                }

    def add_fragment(self, fragment: ChangelogFragment, version: str):
        """
        Add a changelog fragment to the change metadata.
        """
        if fragment.name in self.known_fragments:
            return False

        self.known_fragments.add(fragment.name)

        if 'changes' not in self.releases[version]:
            self.releases[version]['changes'] = dict()
        changes = self.releases[version]['changes']

        if 'fragments' not in self.releases[version]:
            self.releases[version]['fragments'] = []

        for section, lines in fragment.content.items():
            if section == self.config.prelude_name:
                if section in changes:
                    raise ValueError('Found prelude section "{0}" more than once!'.format(section))
                changes[section] = lines
            elif section not in self.config.sections:
                raise ValueError('Found unknown section "{0}"'.format(section))
            else:
                if section not in changes:
                    changes[section] = []
                changes[section].extend(lines)

        self.releases[version]['fragments'].append(fragment.name)
        return True

    @staticmethod
    def _create_plugin_entry(plugin: PluginDescription) -> dict:
        return LegacyPluginResolver.resolve_plugin(plugin)

    def get_plugin_resolver(
            self, plugins: Optional[List[PluginDescription]] = None) -> PluginResolver:
        """
        Create a plugin resolver.

        The plugins list is not used.
        """
        return ChangesDataPluginResolver()

    def get_fragment_resolver(
            self, fragments: Optional[List[ChangelogFragment]] = None) -> FragmentResolver:
        """
        Create a fragment resolver.

        The fragments list is not used.
        """
        return ChangesDataFragmentResolver()

    def _version_or_none(self, version: Optional[str]) -> Optional[Any]:
        return self.version_constructor(version) if version is not None else None

    def prune_versions(self, versions_after: Optional[str],
                       versions_until: Optional[str]) -> None:
        """
        Remove all versions which are not after ``versions_after`` (if provided),
        or which are after ``versions_until`` (if provided).
        """
        versions_after = self._version_or_none(versions_after)
        versions_until = self._version_or_none(versions_until)
        for version in list(self.data['releases']):
            version_obj = self.version_constructor(version)
            if versions_after is not None and version_obj <= versions_after:
                del self.data['releases'][version]
                current_ancestor = self.ancestor
                if current_ancestor is None:
                    self.ancestor = version
                elif self.version_constructor(current_ancestor) < self.version_constructor(version):
                    self.ancestor = version
                continue
            if versions_until is not None and version_obj > versions_until:
                del self.data['releases'][version]
                continue

    @staticmethod
    def concatenate(changes_datas: List['ChangesData']) -> 'ChangesData':
        """
        Concatenate one or more ``ChangesData`` objects.

        The caller is responsible to ensure that every version appears
        in at most one of the provided ``ChangesData`` objects. If this
        is not the case, the behavior is undefined.
        """
        assert len(changes_datas) > 0
        last = changes_datas[-1]
        data = ChangesBase.empty()
        ancestor = None
        no_ancestor = False
        for changes in changes_datas:
            data['releases'].update(changes.data['releases'])
            if not no_ancestor:
                changes_ancestor = changes.ancestor
                if changes_ancestor is None:
                    no_ancestor = True
                    ancestor = None
                elif ancestor is None:
                    ancestor = changes.ancestor
                else:
                    ancestor_ = last.version_constructor(ancestor)
                    changes_ancestor_ = last.version_constructor(changes_ancestor)
                    if ancestor_ > changes_ancestor_:
                        ancestor = changes_ancestor
        data['ancestor'] = ancestor
        return ChangesData(last.config, last.path, data)


def load_changes(config: ChangelogConfig) -> ChangesBase:
    """
    Load changes metadata.
    """
    path = os.path.join(config.paths.changelog_dir, config.changes_file)
    if config.changes_format == 'classic':
        return ChangesMetadata(config, path)
    return ChangesData(config, path)


def add_release(config: ChangelogConfig,  # pylint: disable=too-many-arguments
                changes: ChangesBase,
                plugins: List[PluginDescription],
                fragments: List[ChangelogFragment],
                version: str,
                codename: Optional[str],
                date: datetime.date) -> None:
    """
    Add a release to the change metadata.

    :arg changes: Changes metadata to update
    :arg plugins: List of all plugin descriptions
    :arg fragments: List of all changelog fragments
    :arg version: The version for the new release
    :arg codename: The codename for the new release. Optional for collections
    :arg date: The release date
    """
    # make sure the version parses
    version_constructor = (semantic_version.Version if config.is_collection
                           else packaging.version.Version)
    version_constructor(version)

    LOGGER.info('release version {} is a {} version', version,
                'release' if is_release_version(config, version) else 'pre-release')

    # filter out plugins which were not added in this release
    plugins = list(filter(lambda p: any([
        version.startswith('%s.' % p.version_added),
        version.startswith('%s-' % p.version_added),  # needed for semver
        version.startswith('%s+' % p.version_added),  # needed for semver
        version == p.version_added
    ]), plugins))

    changes.add_release(version, codename, date)

    for plugin in plugins:
        changes.add_plugin(plugin, version)

    fragments_added = []
    for fragment in fragments:
        if changes.add_fragment(fragment, version):
            fragments_added.append(fragment)

    changes.save()

    if not config.keep_fragments:
        for fragment in fragments_added:
            fragment.remove()


def refresh_changelog(config: ChangelogConfig,
                      changes: ChangesBase,
                      plugins: List[PluginDescription],
                      fragments: List[ChangelogFragment]):
    """
    Refresh plugin information and (depending on config) changelog fragments in ``changes``.
    """
    changes.update_plugins(plugins)
    if config.keep_fragments:
        changes.update_fragments(fragments)
    else:
        LOGGER.warning('Cannot refresh changelog fragments, as keep_fragments is false')
    changes.save()

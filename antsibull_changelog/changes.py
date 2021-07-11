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

from typing import Any, Callable, Dict, List, Optional, Set, cast

from .changes_resolvers import (
    FragmentResolver,
    PluginResolver,
    LegacyFragmentResolver,
    LegacyPluginResolver,
    LegacyObjectResolver,
    ChangesDataFragmentResolver,
    ChangesDataPluginResolver,
    ChangesDataObjectResolver
)
from .config import ChangelogConfig
from .fragment import ChangelogFragment, load_fragments
from .logger import LOGGER
from .plugins import PluginDescription, load_plugins
from .sanitize import sanitize_changes
from .utils import get_version_constructor, is_release_version
from .yaml import load_yaml, store_yaml


class ChangesBase(metaclass=abc.ABCMeta):
    """
    Read, write and manage change metadata.
    """

    config: ChangelogConfig
    path: str
    data: dict
    known_plugins: Set[str]
    known_objects: Set[str]
    known_fragments: Set[str]
    ancestor: Optional[str]

    def __init__(self, config: ChangelogConfig, path: str):
        self.config = config
        self.path = path
        self.data = self.empty()
        self.known_fragments = set()
        self.known_plugins = set()
        self.known_objects = set()
        self.ancestor = None

    def version_constructor(self, version: str) -> Any:
        """
        Create a version object.
        """
        return get_version_constructor(self.config)(version)

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
            self.data = sanitize_changes(data_override, config=self.config)
        elif os.path.exists(self.path):
            self.data = sanitize_changes(load_yaml(self.path), config=self.config)
        else:
            self.data = self.empty()
        self.ancestor = self.data.get('ancestor')

    @abc.abstractmethod
    def update_plugins(self, plugins: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """

    @abc.abstractmethod
    def update_objects(self, objects: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update object descriptions, and remove objects which are not in the provided list
        of objects.
        """

    @abc.abstractmethod
    def update_fragments(self, fragments: List[ChangelogFragment],
                         load_extra_fragments: Optional[
                             Callable[[str], List[ChangelogFragment]]] = None
                         ) -> None:
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

    def add_release(self, version: str, codename: Optional[str],
                    release_date: datetime.date, update_existing=False):
        """
        Add a new releases to the changes metadata.
        """
        if version not in self.releases:
            self.releases[version] = dict()
        elif not update_existing:
            LOGGER.warning('release {} already exists', version)
            return

        self.releases[version]['release_date'] = release_date.isoformat()
        if codename is not None:
            self.releases[version]['codename'] = codename

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
        if plugin.category != 'plugin':
            return False

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

    def add_object(self, ansible_object: PluginDescription, version: str):
        """
        Add a new object to the change metadata for the given version.

        If the object happens to be already known (for another version),
        it will not be added.

        :return: ``True`` if the object was added for this version
        """
        if ansible_object.category != 'object':
            return False

        composite_name = '%s/%s' % (ansible_object.type, ansible_object.name)

        if composite_name in self.known_objects:
            return False

        self.known_objects.add(composite_name)

        if 'objects' not in self.releases[version]:
            self.releases[version]['objects'] = {}

        objects = self.releases[version]['objects']

        if ansible_object.type not in objects:
            objects[ansible_object.type] = []

        objects[ansible_object.type].append(self._create_plugin_entry(ansible_object))

        return True

    @abc.abstractmethod
    def get_plugin_resolver(
            self, plugins: Optional[List[PluginDescription]] = None) -> PluginResolver:
        """
        Create a plugin resolver.

        If the plugins are not provided and needed by this object, they might be loaded.
        """

    @abc.abstractmethod
    def get_object_resolver(self) -> PluginResolver:
        """
        Create a object resolver.
        """

    @abc.abstractmethod
    def get_fragment_resolver(
            self, fragments: Optional[List[ChangelogFragment]] = None) -> FragmentResolver:
        """
        Create a fragment resolver.

        If the fragments are not provided and needed by this object, they might be loaded.
        """


class ChangesMetadata(ChangesBase):
    """
    Read, write and manage classic Ansible (2.9 and earlier) change metadata.
    """

    def __init__(self, config: ChangelogConfig, path: str):
        """
        Create legacy change metadata.
        """
        super().__init__(config, path)
        self.load()

    def load(self, data_override: Optional[dict] = None) -> None:
        """
        Load the change metadata from disk.
        """
        super().load(data_override=data_override)

        for _, config in self.releases.items():
            for plugin_type, plugin_names in config.get('plugins', {}).items():
                self.known_plugins |= set(
                    '%s/%s' % (plugin_type, plugin_name) for plugin_name in plugin_names)

            module_names = config.get('modules', [])

            self.known_plugins |= set('module/%s' % module_name for module_name in module_names)

            self.known_fragments |= set(config.get('fragments', []))

    def update_plugins(self, plugins: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """
        if not allow_removals:
            # We only remove here, we don't update, since we only keep references
            # to the plugins.
            return

        valid_plugins = collections.defaultdict(set)

        for plugin in plugins:
            if plugin.category == 'plugin':
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

    def update_objects(self, objects: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update object descriptions, and remove objects which are not in the provided list
        of objects.
        """
        return

    def update_fragments(self, fragments: List[ChangelogFragment],
                         load_extra_fragments: Optional[
                             Callable[[str], List[ChangelogFragment]]] = None
                         ) -> None:
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

    def get_object_resolver(self) -> PluginResolver:
        """
        Create a dummy object resolver.
        """
        return LegacyObjectResolver()

    def get_fragment_resolver(
            self, fragments: Optional[List[ChangelogFragment]] = None) -> FragmentResolver:
        """
        Create a fragment resolver.

        If the fragments are not provided and needed by this object, they **will** be loaded.
        """
        if fragments is None:
            fragments = load_fragments(paths=self.config.paths, config=self.config)
        return LegacyFragmentResolver(fragments)


class ChangesData(ChangesBase):
    """
    Read, write and manage modern change metadata.

    This is the format used for ansible-base 2.10, ansible-core 2.11+, and for Ansible collections.
    """

    config: ChangelogConfig

    def __init__(self, config: ChangelogConfig, path: str, data_override: Optional[dict] = None):
        """
        Create modern change metadata.

        :arg data_override: Allows to load data from dictionary instead from disk
        """
        super().__init__(config, path)
        self.config = config
        self.load(data_override=data_override)

    def load(self, data_override: Optional[dict] = None) -> None:
        """
        Load the change metadata from disk.
        """
        super().load(data_override=data_override)

        for _, config in self.releases.items():
            for plugin_type, plugins in config.get('plugins', {}).items():
                self.known_plugins |= set(
                    '%s/%s' % (plugin_type, plugin['name']) for plugin in plugins)

            for object_type, objects in config.get('objects', {}).items():
                self.known_objects |= set(
                    '%s/%s' % (object_type, ansible_object['name']) for ansible_object in objects)

            modules = config.get('modules', [])

            self.known_plugins |= set('module/%s' % module['name'] for module in modules)

            self.known_fragments |= set(config.get('fragments', []))

    def update_plugins(self, plugins: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update plugin descriptions, and remove plugins which are not in the provided list
        of plugins.
        """
        valid_plugins: Dict[str, Dict[str, PluginDescription]] = collections.defaultdict(dict)

        for plugin in plugins:
            if plugin.category == 'plugin':
                valid_plugins[plugin.type][plugin.name] = plugin

        for _, config in self.releases.items():
            if 'modules' in config:
                invalid_module_names = set(
                    module['name'] for module in config['modules']
                    if module['name'] not in valid_plugins['module'])
                if allow_removals:
                    config['modules'] = [
                        self._create_plugin_entry(valid_plugins['module'][module['name']])
                        for module in config['modules']
                        if module['name'] not in invalid_module_names]
                    self.known_plugins -= set(
                        'module/%s' % module_name for module_name in invalid_module_names)
                else:
                    config['modules'] = [
                        self._create_plugin_entry(valid_plugins['module'][module['name']])
                        if module['name'] not in invalid_module_names else
                        module
                        for module in config['modules']]

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    invalid_plugin_names = set(
                        plugin['name'] for plugin in config['plugins'][plugin_type]
                        if plugin['name'] not in valid_plugins[plugin_type])
                    if allow_removals:
                        config['plugins'][plugin_type] = [
                            self._create_plugin_entry(valid_plugins[plugin_type][plugin['name']])
                            for plugin in config['plugins'][plugin_type]
                            if plugin['name'] not in invalid_plugin_names]
                        self.known_plugins -= set(
                            '%s/%s' % (plugin_type, plugin_name)
                            for plugin_name in invalid_plugin_names)
                    else:
                        config['plugins'][plugin_type] = [
                            self._create_plugin_entry(valid_plugins[plugin_type][plugin['name']])
                            if plugin['name'] not in invalid_plugin_names else
                            plugin
                            for plugin in config['plugins'][plugin_type]]

    def update_objects(self, objects: List[PluginDescription],
                       allow_removals: Optional[bool]) -> None:
        """
        Update object descriptions, and remove objects which are not in the provided list
        of objects.
        """
        valid_objects: Dict[str, Dict[str, PluginDescription]] = collections.defaultdict(dict)

        for ansible_object in objects:
            if ansible_object.category == 'object':
                valid_objects[ansible_object.type][ansible_object.name] = ansible_object

        for _, config in self.releases.items():
            if 'objects' in config:
                for object_type in config['objects']:
                    invalid_object_names = set(
                        ansible_object['name'] for ansible_object in config['objects'][object_type]
                        if ansible_object['name'] not in valid_objects[object_type])
                    if allow_removals:
                        config['objects'][object_type] = [
                            self._create_plugin_entry(
                                valid_objects[object_type][ansible_object['name']])
                            for ansible_object in config['objects'][object_type]
                            if ansible_object['name'] not in invalid_object_names]
                        self.known_objects -= set(
                            '%s/%s' % (object_type, object_name)
                            for object_name in invalid_object_names)
                    else:
                        config['objects'][object_type] = [
                            self._create_plugin_entry(
                                valid_objects[object_type][ansible_object['name']])
                            if ansible_object['name'] not in invalid_object_names else
                            ansible_object
                            for ansible_object in config['objects'][object_type]]

    def update_fragments(self, fragments: List[ChangelogFragment],
                         load_extra_fragments: Optional[
                             Callable[[str], List[ChangelogFragment]]] = None
                         ) -> None:
        """
        Update fragment contents, and remove fragment contents which are not in the provided
        list of fragments.

        Must only be called if ``keep_fragments`` is set to ``True`` in the configuration,
        or if ``load_extra_fragments`` is provided.
        """
        assert self.config.keep_fragments or load_extra_fragments
        valid_fragments_global = {fragment.name: fragment for fragment in fragments}
        for version, config in self.releases.items():
            valid_fragments = dict(valid_fragments_global)
            if load_extra_fragments:
                extra_fragments = load_extra_fragments(version)
                valid_fragments.update({fragment.name: fragment for fragment in extra_fragments})

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
                    valid_fragments[fragment] for fragment in config['fragments']],
                    ignore_obj_adds=True)

    def sort(self) -> None:
        """
        Sort change metadata in place.
        """
        super().sort()

        for _, config in self.data['releases'].items():
            if 'modules' in config:
                config['modules'] = sorted(config['modules'], key=lambda module: module['name'])

            if 'plugins' in config:
                for plugin_type in config['plugins']:
                    config['plugins'][plugin_type] = sorted(
                        config['plugins'][plugin_type], key=lambda plugin: plugin['name'])

            if 'objects' in config:
                for object_type in config['objects']:
                    config['objects'][object_type] = sorted(
                        config['objects'][object_type],
                        key=lambda ansible_object: ansible_object['name'])

            if 'fragments' in config:
                config['fragments'] = sorted(config['fragments'])

            if 'changes' in config:
                config['changes'] = {
                    section: sorted(entries) if section != self.config.prelude_name else entries
                    for section, entries in sorted(config['changes'].items())
                }

    def _add_fragment_obj(self, obj_class, obj_type, entry, version: str):
        """
        Add an object or a plugin from a changelog fragment.
        """
        if obj_class == 'object':
            composite_name = '%s/%s' % (obj_type, entry['name'])
            if composite_name in self.known_objects:
                LOGGER.warning(
                    'Ignore adding %s object "%s" from changelog fragment' % (
                        obj_type, entry['name']))
                return
            self.known_objects.add(composite_name)
            toplevel_type = 'objects'
            has_categories = True
        if obj_class == 'plugin':
            composite_name = '%s/%s' % (obj_type, entry['name'])
            if composite_name in self.known_plugins:
                LOGGER.warning(
                    'Ignore adding %s plugin "%s" from changelog fragment' % (
                        obj_type, entry['name']))
                return
            self.known_plugins.add(composite_name)
            if obj_type == 'module':
                toplevel_type = 'modules'
                has_categories = False
            else:
                toplevel_type = 'plugins'
                has_categories = True

        if has_categories:
            if toplevel_type not in self.releases[version]:
                self.releases[version][toplevel_type] = {}

            categories = self.releases[version][toplevel_type]

            if obj_type not in categories:
                categories[obj_type] = []

            obj_list = categories[obj_type]
        else:
            if toplevel_type not in self.releases[version]:
                self.releases[version][toplevel_type] = []

            obj_list = self.releases[version][toplevel_type]

        obj_list.append({
            'name': entry['name'],
            'description': entry['description'],
            'namespace': entry.get('namespace'),
        })

    def _add_fragment_content(self, version: str, changes: Dict[str, Any],
                              section: str, lines: Any):
        """
        Add contents of a changelog fragment. Helps implementing add_fragment().
        """
        if section == self.config.prelude_name:
            if section in changes:
                raise ValueError('Found prelude section "{0}" more than once!'.format(section))
            changes[section] = lines
        elif section == self.config.trivial_section_name:
            # Ignore trivial section entries
            return
        elif section.startswith('add') and '.' in section:
            obj_class, obj_type = section[4:].split('.', 1)
            for entry in lines:
                self._add_fragment_obj(obj_class, obj_type, entry, version)
        elif section not in self.config.sections:
            raise ValueError('Found unknown section "{0}"'.format(section))
        else:
            if section not in changes:
                changes[section] = []
            changes[section].extend(lines)

    def add_fragment(self, fragment: ChangelogFragment, version: str):
        """
        Add a changelog fragment to the change metadata.
        """
        if fragment.name in self.known_fragments and self.config.prevent_known_fragments:
            return False

        self.known_fragments.add(fragment.name)

        if 'changes' not in self.releases[version]:
            self.releases[version]['changes'] = dict()
        changes = self.releases[version]['changes']

        if 'fragments' not in self.releases[version]:
            self.releases[version]['fragments'] = []

        for section, lines in fragment.content.items():
            self._add_fragment_content(version, changes, section, lines)

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

    def get_object_resolver(self) -> PluginResolver:
        """
        Create a object resolver.
        """
        return ChangesDataObjectResolver()

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


def _filter_version_exact(version: str, version_added: Optional[str]) -> bool:
    return bool(version_added) and any([
        version.startswith('%s.' % version_added),
        version.startswith('%s-' % version_added),  # needed for semver
        version.startswith('%s+' % version_added),  # needed for semver
        version == version_added
    ])


def _create_filter_version_range(prev_version: str, current_version: str, config: ChangelogConfig
                                 ) -> Callable[[Optional[str]], bool]:
    version_constructor = get_version_constructor(config)
    prev_version_ = version_constructor(prev_version)
    current_version_ = version_constructor(current_version)

    def f(version_added: Optional[str]) -> bool:
        if not version_added:
            return False
        version_added_ = version_constructor(version_added)
        return prev_version_ < version_added_ <= current_version_

    return f


def _add_plugins_filters(changes: ChangesBase,
                         plugins: List[PluginDescription],
                         objects: List[PluginDescription],
                         version: str,
                         prev_version: Optional[str],
                         ) -> None:
    if prev_version is None:
        def version_filter(obj: PluginDescription) -> bool:
            return _filter_version_exact(version, obj.version_added)
    else:
        inner_version_filter = _create_filter_version_range(prev_version, version, changes.config)

        def version_filter(obj: PluginDescription) -> bool:
            return inner_version_filter(obj.version_added)

    # filter out plugins which were not added in this release
    plugins = [
        plugin for plugin in plugins
        if version_filter(plugin) and plugin.category == 'plugin'
    ]

    # filter out objects which were not added in this release
    objects = [
        ansible_object for ansible_object in objects
        if version_filter(ansible_object) and ansible_object.category == 'object'
    ]

    for plugin in plugins:
        changes.add_plugin(plugin, version)

    for ansible_object in objects:
        changes.add_object(ansible_object, version)


def _add_fragments(changes: ChangesBase,
                   fragments: List[ChangelogFragment],
                   version: str,
                   show_release_summary_warning: bool
                   ) -> List[ChangelogFragment]:
    fragments_added = []
    has_release_summary = False
    for fragment in fragments:
        if changes.add_fragment(fragment, version):
            fragments_added.append(fragment)
            if changes.config.prelude_name in fragment.content:
                has_release_summary = True

    if not has_release_summary and show_release_summary_warning:
        LOGGER.warning(
            'Found no {} section in the changelog for this release. While this is not required,'
            ' we suggest to add one with basic information on the release.'.format(
                changes.config.prelude_name))

    return fragments_added


def add_release(config: ChangelogConfig,  # pylint: disable=too-many-arguments,too-many-locals
                changes: ChangesBase,
                plugins: List[PluginDescription],
                fragments: List[ChangelogFragment],
                version: str,
                codename: Optional[str],
                date: datetime.date,
                save_changes: bool = True,
                update_existing: bool = False,
                objects: Optional[List[PluginDescription]] = None,
                prev_version: Optional[str] = None,
                show_release_summary_warning: bool = True,
                ) -> None:
    """
    Add a release to the change metadata.

    :arg changes: Changes metadata to update
    :arg plugins: List of all plugin descriptions
    :arg objects: List of all object descriptions
    :arg fragments: List of all changelog fragments
    :arg version: The version for the new release
    :arg codename: The codename for the new release. Optional for collections
    :arg date: The release date
    :arg update_existing: When set to ``True``, will update an existing release
                          instead of ignoring it
    :arg prev_version: When provided, all plugins added after prev_version are included, and not
                       only the ones added in this version.
    :arg show_release_summary_warning: When set to ``True``, show a warning when the release has
                                       no ``release_summary``.
    """
    # for backwards compatibility, objects can be None
    if objects is None:
        objects = []

    # make sure the version parses
    version_constructor = get_version_constructor(config)
    version_constructor(version)

    LOGGER.info('release version {} is a {} version', version,
                'release' if is_release_version(config, version) else 'pre-release')

    changes.add_release(version, codename, date, update_existing=update_existing)

    _add_plugins_filters(changes, plugins, objects, version, prev_version)

    fragments_added = _add_fragments(changes, fragments, version, show_release_summary_warning)

    if save_changes:
        changes.save()

    if not config.keep_fragments:
        archive_path_template = config.archive_path_template
        if archive_path_template is None:
            # Actually remove fragments
            for fragment in fragments_added:
                fragment.remove()
        else:
            # Move fragments
            archive_path = os.path.join(
                config.paths.base_dir, archive_path_template.format(version=version))
            os.makedirs(archive_path, exist_ok=True)
            for fragment in fragments_added:
                fragment.move_to(archive_path)

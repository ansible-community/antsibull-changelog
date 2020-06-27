# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Generate reStructuredText changelog from ChangesBase instance.
"""

import collections
import os

from typing import Any, Dict, List, MutableMapping, Optional, Union

import packaging.version
import semantic_version

from .changes import ChangesBase, FragmentResolver, PluginResolver
from .config import ChangelogConfig, PathsConfig
from .fragment import ChangelogFragment
from .logger import LOGGER
from .plugins import PluginDescription
from .rst import RstBuilder
from .utils import is_release_version


class ChangelogEntry:
    """
    Data for a changelog entry.
    """

    version: str

    modules: List[Any]
    plugins: Dict[Any, Any]
    changes: Dict[str, Union[str, List[str]]]

    def __init__(self, version: str):
        self.version = version
        self.modules = []
        self.plugins = dict()
        self.changes = dict()

    def has_no_changes(self, section_names: Optional[List[str]] = None) -> bool:
        """
        Determine whether there are changes.

        If ``section_names`` is not supplied, all sections will be checked.
        """
        if section_names is None:
            return all(not content for content in self.changes)
        return all(not self.changes.get(section_name) for section_name in section_names)

    @property
    def empty(self) -> bool:
        """
        Determine whether the entry has no content at all.
        """
        return not self.modules and not self.plugins and self.has_no_changes()

    def add_section_content(self,
                            builder: RstBuilder,
                            section_name: str) -> None:
        """
        Add a section's content of fragments to the changelog.
        """
        if section_name not in self.changes:
            return

        content = self.changes[section_name]

        if isinstance(content, list):
            for rst in sorted(content):
                builder.add_list_item(rst)
        else:
            builder.add_raw_rst(content)


class ChangelogGenerator:
    """
    Generate changelog as reStructuredText.

    This class can be both used to create a full changelog, or to append a
    changelog to an existing RstBuilder. This is for example useful to create
    a combined ACD changelog.
    """

    config: ChangelogConfig
    changes: ChangesBase
    plugin_resolver: PluginResolver
    fragment_resolver: FragmentResolver

    def __init__(self,  # pylint: disable=too-many-arguments
                 config: ChangelogConfig,
                 changes: ChangesBase,
                 plugins: Optional[List[PluginDescription]] = None,
                 fragments: Optional[List[ChangelogFragment]] = None,
                 flatmap: bool = True):
        """
        Create a changelog generator.
        """
        self.config = config
        self.changes = changes
        self.flatmap = flatmap

        self.plugin_resolver = changes.get_plugin_resolver(plugins)
        self.fragment_resolver = changes.get_fragment_resolver(fragments)

    def version_constructor(self, version: str) -> Any:
        """
        Create a version object.
        """
        if self.config.is_collection:
            return semantic_version.Version(version)
        return packaging.version.Version(version)

    def _collect_versions(self, after_version: Optional[str] = None,
                          until_version: Optional[str] = None) -> List[str]:
        """
        Collect all versions of interest and return them as an ordered list,
        latest to earliest.
        """
        result = []
        for version in sorted(self.changes.releases, reverse=True, key=self.version_constructor):
            if after_version is not None:
                if self.version_constructor(version) <= self.version_constructor(after_version):
                    continue
            if until_version is not None:
                if self.version_constructor(version) > self.version_constructor(until_version):
                    continue
            result.append(version)
        return result

    @staticmethod
    def _get_entry_config(release_entries: MutableMapping[str, ChangelogEntry],
                          entry_version: str) -> ChangelogEntry:
        """
        Create (if not existing) and return release entry for a given version.
        """
        if entry_version not in release_entries:
            release_entries[entry_version] = ChangelogEntry(entry_version)

        return release_entries[entry_version]

    def _update_modules_plugins(self, entry_config: ChangelogEntry, release: dict) -> None:
        """
        Update a release entry given a release information dict.
        """
        plugins = self.plugin_resolver.resolve(release)

        if 'module' in plugins:
            entry_config.modules += plugins.pop('module')

        for plugin_type, plugin_list in plugins.items():
            if plugin_type not in entry_config.plugins:
                entry_config.plugins[plugin_type] = []

            entry_config.plugins[plugin_type] += plugin_list

    def collect(self, squash: bool = False, after_version: Optional[str] = None,
                until_version: Optional[str] = None) -> List[ChangelogEntry]:
        """
        Collect release entries.

        :arg squash: Squash all releases into one entry
        :arg after_version: If given, only consider versions after this one
        :arg until_version: If given, do not consider versions following this one
        :return: An ordered mapping of versions to release entries
        """
        release_entries: MutableMapping[str, ChangelogEntry] = collections.OrderedDict()
        entry_version = until_version or self.changes.latest_version
        entry_fragment = None

        for version in self._collect_versions(
                after_version=after_version, until_version=until_version):
            release = self.changes.releases[version]

            if not squash:
                if is_release_version(self.config, version):
                    # next version is a release, it needs its own entry
                    entry_version = version
                    entry_fragment = None
                elif not is_release_version(self.config, entry_version):
                    # current version is a pre-release, next version needs its own entry
                    entry_version = version
                    entry_fragment = None

            entry_config = self._get_entry_config(release_entries, entry_version)

            dest_changes = entry_config.changes

            for fragment in self.fragment_resolver.resolve(release):
                for section, lines in fragment.content.items():
                    if section == self.config.prelude_name:
                        if entry_fragment:
                            LOGGER.info('skipping prelude in version {} due to newer '
                                        'prelude in version {}',
                                        version, entry_version)
                            continue

                        # lines is a str in this case!
                        entry_fragment = lines
                        dest_changes[section] = lines
                    else:
                        content = dest_changes.get(section)
                        if isinstance(content, list):
                            content.extend(lines)
                        else:
                            dest_changes[section] = list(lines)

            self._update_modules_plugins(entry_config, release)

        return list(release_entries.values())

    def append_changelog_entry(self, builder: RstBuilder,
                               changelog_entry: ChangelogEntry,
                               start_level: int = 0,
                               add_version: bool = False) -> None:
        """
        Append changelog entry to a reStructuredText (RST) builder.

        :arg start_level: Level to add to headings in the generated RST
        """
        if add_version:
            builder.add_section('v%s' % changelog_entry.version, start_level)

        for section_name in self.config.sections:
            self._add_section(builder, changelog_entry, section_name, start_level=start_level)

        self._add_plugins(builder, changelog_entry.plugins, start_level=start_level)
        self._add_modules(builder, changelog_entry.modules, flatmap=self.flatmap,
                          start_level=start_level)

    def generate_to(self,  # pylint: disable=too-many-arguments
                    builder: RstBuilder,
                    start_level: int = 0,
                    squash: bool = False,
                    after_version: Optional[str] = None,
                    until_version: Optional[str] = None) -> None:
        """
        Append changelog to a reStructuredText (RST) builder.

        :arg start_level: Level to add to headings in the generated RST
        :arg squash: Squash all releases into one entry
        :arg after_version: If given, only consider versions after this one
        :arg until_version: If given, do not consider versions following this one
        """
        release_entries = self.collect(
            squash=squash, after_version=after_version, until_version=until_version)

        for release in release_entries:
            self.append_changelog_entry(
                builder, release, start_level=start_level, add_version=not squash)

    def generate(self) -> str:
        """
        Generate the changelog as reStructuredText.
        """
        latest_version = self.changes.latest_version
        codename = self.changes.releases[latest_version].get('codename')
        major_minor_version = '.'.join(
            latest_version.split('.')[:self.config.changelog_filename_version_depth])

        builder = RstBuilder()
        title = self.config.title or 'Ansible'
        if major_minor_version:
            title = '%s %s' % (title, major_minor_version)
        if codename:
            title = '%s "%s"' % (title, codename)
        builder.set_title('%s Release Notes' % (title,))
        builder.add_raw_rst('.. contents:: Topics\n')

        if self.changes.ancestor and self.config.mention_ancestor:
            builder.add_raw_rst(
                'This changelog describes changes after version {0}.\n'
                .format(self.changes.ancestor))
        else:
            builder.add_raw_rst('')

        self.generate_to(builder, 0)

        return builder.generate()

    def _add_section(self, builder: RstBuilder,
                     changelog_entry: ChangelogEntry,
                     section_name: str,
                     start_level: int) -> None:
        """
        Add a section of fragments to the changelog.
        """
        if section_name not in changelog_entry.changes:
            return

        section_title = self.config.sections[section_name]
        builder.add_section(section_title, start_level + 1)

        changelog_entry.add_section_content(builder, section_name)

        builder.add_raw_rst('')

    @staticmethod
    def _add_plugins(builder: RstBuilder,
                     plugins_database: Dict[str, List[Dict[str, Any]]],
                     start_level: int = 0) -> None:
        """
        Add new plugins to the changelog.
        """
        if not plugins_database:
            return

        have_section = False

        for plugin_type in sorted(plugins_database):
            plugins = plugins_database.get(plugin_type)
            if not plugins:
                continue

            if not have_section:
                have_section = True
                builder.add_section('New Plugins', start_level + 1)

            builder.add_section(plugin_type.title(), start_level + 2)

            for plugin in sorted(plugins, key=lambda plugin: plugin['name']):
                builder.add_raw_rst('- %s - %s' % (plugin['name'], plugin['description']))

            builder.add_raw_rst('')

    @staticmethod
    def _add_modules(builder: RstBuilder,
                     modules: List[Dict[str, Any]],
                     flatmap: bool,
                     start_level: int = 0) -> None:
        """
        Add new modules to the changelog.
        """
        if not modules:
            return

        modules_by_namespace = collections.defaultdict(list)
        for module in sorted(modules, key=lambda module: module['name']):
            modules_by_namespace[module['namespace']].append(module)

        previous_section = None
        for namespace in sorted(modules_by_namespace):
            parts = namespace.split('.')

            section = parts.pop(0).replace('_', ' ').title()

            if previous_section is None:
                builder.add_section('New Modules', start_level + 1)

            if section != previous_section and section:
                builder.add_section(section, start_level + 2)

            previous_section = section

            subsection = '.'.join(parts)

            if subsection:
                builder.add_section(subsection, start_level + 3)

            for module in modules_by_namespace[namespace]:
                module_name = module['name']
                if not flatmap and namespace:
                    module_name = '%s.%s' % (namespace, module_name)

                builder.add_raw_rst('- %s - %s' % (module_name, module['description']))

            builder.add_raw_rst('')


def generate_changelog(paths: PathsConfig,  # pylint: disable=too-many-arguments
                       config: ChangelogConfig,
                       changes: ChangesBase,
                       plugins: Optional[List[PluginDescription]] = None,
                       fragments: Optional[List[ChangelogFragment]] = None,
                       flatmap: bool = True):
    """
    Generate the changelog as reStructuredText.

    :arg plugins: Will be loaded if necessary. Only provide when you already have them
    :arg fragments: Will be loaded if necessary. Only provide when you already have them
    :type flatmap: Whether the collection uses flatmapping or not
    """
    major_minor_version = '.'.join(
        changes.latest_version.split('.')[:config.changelog_filename_version_depth])
    if '%s' in config.changelog_filename_template:
        changelog_filename = config.changelog_filename_template % (major_minor_version, )
    else:
        changelog_filename = config.changelog_filename_template
    changelog_path = os.path.join(paths.changelog_dir, changelog_filename)

    generator = ChangelogGenerator(config, changes, plugins, fragments, flatmap)
    rst = generator.generate()

    with open(changelog_path, 'wb') as changelog_fd:
        changelog_fd.write(rst.encode('utf-8'))

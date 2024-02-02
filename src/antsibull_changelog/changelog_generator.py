# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Generate reStructuredText changelog from ChangesBase instance.
"""

from __future__ import annotations

import abc
import collections
import os
from collections.abc import MutableMapping
from typing import Any, cast

from .changes import ChangesBase, FragmentResolver, PluginResolver
from .config import ChangelogConfig, PathsConfig, TextFormat
from .fragment import ChangelogFragment
from .logger import LOGGER
from .plugins import PluginDescription
from .rst import RstBuilder
from .utils import collect_versions


class ChangelogEntry:
    """
    Data for a changelog entry.
    """

    version: str
    text_format: TextFormat

    modules: list[Any]
    plugins: dict[Any, Any]
    objects: dict[Any, Any]
    changes: dict[str, str | list[str]]
    preludes: list[tuple[str, str]]

    def __init__(self, version: str):
        self.version = version
        self.text_format = TextFormat.RESTRUCTURED_TEXT
        self.modules = []
        self.plugins = {}
        self.objects = {}
        self.changes = {}
        self.preludes = []

    def has_no_changes(self, section_names: list[str] | None = None) -> bool:
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
        return (
            not self.modules
            and not self.plugins
            and not self.objects
            and not self.preludes
            and self.has_no_changes()
        )

    def add_section_content(self, builder: RstBuilder, section_name: str) -> None:
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


def get_entry_config(
    release_entries: MutableMapping[str, ChangelogEntry], entry_version: str
) -> ChangelogEntry:
    """
    Create (if not existing) and return release entry for a given version.
    """
    if entry_version not in release_entries:
        release_entries[entry_version] = ChangelogEntry(entry_version)

    return release_entries[entry_version]


class ChangelogGeneratorBase(abc.ABC):
    """
    Abstract base class for changelog generators.

    Provides some useful helpers.
    """

    config: ChangelogConfig
    changes: ChangesBase
    plugin_resolver: PluginResolver
    fragment_resolver: FragmentResolver

    def __init__(  # pylint: disable=too-many-arguments
        self,
        config: ChangelogConfig,
        changes: ChangesBase,
        /,
        plugins: list[PluginDescription] | None = None,
        fragments: list[ChangelogFragment] | None = None,
        flatmap: bool = True,
    ):
        """
        Create a changelog generator.
        """
        self.config = config
        self.changes = changes
        self.flatmap = flatmap

        self.plugin_resolver = changes.get_plugin_resolver(plugins)
        self.object_resolver = changes.get_object_resolver()
        self.fragment_resolver = changes.get_fragment_resolver(fragments)

    def _update_modules_plugins_objects(
        self, entry_config: ChangelogEntry, release: dict
    ) -> None:
        """
        Update a release entry given a release information dict.
        """
        plugins = self.plugin_resolver.resolve(release)
        objects = self.object_resolver.resolve(release)

        if "module" in plugins:
            entry_config.modules += plugins.pop("module")

        for plugin_type, plugin_list in plugins.items():
            if plugin_type not in entry_config.plugins:
                entry_config.plugins[plugin_type] = []

            entry_config.plugins[plugin_type] += plugin_list

        for object_type, object_list in objects.items():
            if object_type not in entry_config.objects:
                entry_config.objects[object_type] = []

            entry_config.objects[object_type] += object_list

    def _collect_entry(
        self, entry_config: ChangelogEntry, entry_version: str, versions: list[str]
    ) -> None:
        """
        Do actual work of collecting data for a changelog entry.
        """
        entry_fragment = None

        dest_changes = entry_config.changes

        for version in versions:
            release = self.changes.releases[version]

            for fragment in self.fragment_resolver.resolve(release):
                for section, lines in fragment.content.items():
                    if section == self.config.prelude_name:
                        prelude_content = cast(str, lines)
                        entry_config.preludes.append((version, prelude_content))

                        if entry_fragment:
                            LOGGER.info(
                                "skipping prelude in version {} due to newer "
                                "prelude in version {}",
                                version,
                                entry_version,
                            )
                            continue

                        # lines is a str in this case!
                        entry_fragment = prelude_content
                        dest_changes[section] = prelude_content
                    else:
                        content = dest_changes.get(section)
                        if isinstance(content, list):
                            content.extend(lines)
                        else:
                            dest_changes[section] = list(lines)

            self._update_modules_plugins_objects(entry_config, release)

    def collect(
        self,
        squash: bool = False,
        after_version: str | None = None,
        until_version: str | None = None,
    ) -> list[ChangelogEntry]:
        """
        Collect release entries.

        :arg squash: Squash all releases into one entry
        :arg after_version: If given, only consider versions after this one
        :arg until_version: If given, do not consider versions following this one
        :return: An ordered mapping of versions to release entries
        """
        release_entries: MutableMapping[str, ChangelogEntry] = collections.OrderedDict()

        for entry_version, versions in collect_versions(
            self.changes.releases,
            self.config,
            after_version=after_version,
            until_version=until_version,
            squash=squash,
        ):
            entry_config = get_entry_config(release_entries, entry_version)
            self._collect_entry(entry_config, entry_version, versions)

        return list(release_entries.values())

    def get_fqcn_prefix(self) -> str | None:
        """
        Returns the FQCN prefix (collection name) for plugins/modules.
        """
        fqcn_prefix = None
        if self.config.use_fqcn:
            if self.config.paths.is_collection:
                fqcn_prefix = "%s.%s" % (
                    self.config.collection_details.get_namespace(),
                    self.config.collection_details.get_name(),
                )
            else:
                fqcn_prefix = "ansible.builtin"
        return fqcn_prefix

    def get_title(self) -> str:
        """
        Return changelog's title.
        """
        latest_version = self.changes.latest_version
        codename = self.changes.releases[latest_version].get("codename")
        major_minor_version = ".".join(
            latest_version.split(".")[: self.config.changelog_filename_version_depth]
        )

        title = self.config.title or "Ansible"
        if major_minor_version:
            title = "%s %s" % (title, major_minor_version)
        if codename:
            title = '%s "%s"' % (title, codename)
        return "%s Release Notes" % (title,)


def get_plugin_name(
    name: str,
    /,
    fqcn_prefix: str | None = None,
    namespace: str | None = None,
    flatmap: bool = False,
) -> str:
    """
    Given a module or plugin name, prepends FQCN prefix (collection name) and/or namespace,
    if appropriate.
    """
    if not flatmap and namespace:
        name = "%s.%s" % (namespace, name)
    if fqcn_prefix:
        name = "%s.%s" % (fqcn_prefix, name)
    return name


class ChangelogGenerator(ChangelogGeneratorBase):
    # antsibull_changelog.rendering.changelog.ChangelogGenerator is a modified
    # copy of this class adjust to the document rendering framework in
    # antsibull_changelog.rendering. To avoid pylint complaining too much, we
    # disable 'duplicate-code' for this class.

    # pylint: disable=duplicate-code

    """
    Generate changelog as reStructuredText.

    This class can be both used to create a full changelog, or to append a
    changelog to an existing RstBuilder. This is for example useful to create
    a combined ACD changelog.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        config: ChangelogConfig,
        changes: ChangesBase,
        plugins: list[PluginDescription] | None = None,
        fragments: list[ChangelogFragment] | None = None,
        flatmap: bool = True,
    ):
        """
        Create a changelog generator.
        """
        super().__init__(
            config, changes, plugins=plugins, fragments=fragments, flatmap=flatmap
        )

    def append_changelog_entry(
        self,
        builder: RstBuilder,
        changelog_entry: ChangelogEntry,
        start_level: int = 0,
        add_version: bool = False,
    ) -> None:
        """
        Append changelog entry to a reStructuredText (RST) builder.

        :arg start_level: Level to add to headings in the generated RST
        """
        if add_version:
            builder.add_section("v%s" % changelog_entry.version, start_level)

        for section_name in self.config.sections:
            self._add_section(
                builder, changelog_entry, section_name, start_level=start_level
            )

        fqcn_prefix = self.get_fqcn_prefix()
        self._add_plugins(
            builder,
            changelog_entry.plugins,
            fqcn_prefix=fqcn_prefix,
            start_level=start_level,
        )
        self._add_modules(
            builder,
            changelog_entry.modules,
            flatmap=self.flatmap,
            fqcn_prefix=fqcn_prefix,
            start_level=start_level,
        )
        self._add_objects(
            builder,
            changelog_entry.objects,
            fqcn_prefix=fqcn_prefix,
            start_level=start_level,
        )

    def generate_to(  # pylint: disable=too-many-arguments
        self,
        builder: RstBuilder,
        start_level: int = 0,
        squash: bool = False,
        after_version: str | None = None,
        until_version: str | None = None,
        only_latest: bool = False,
    ) -> None:
        """
        Append changelog to a reStructuredText (RST) builder.

        :arg start_level: Level to add to headings in the generated RST
        :arg squash: Squash all releases into one entry
        :arg after_version: If given, only consider versions after this one
        :arg until_version: If given, do not consider versions following this one
        :arg only_latest: If set to ``True``, only generate the latest entry
        """
        release_entries = self.collect(
            squash=squash, after_version=after_version, until_version=until_version
        )

        for release in release_entries:
            self.append_changelog_entry(
                builder,
                release,
                start_level=start_level,
                add_version=not squash and not only_latest,
            )
            if only_latest:
                break

    def generate(self, only_latest: bool = False) -> str:
        """
        Generate the changelog as reStructuredText.
        """
        builder = RstBuilder()

        if not only_latest:
            builder.set_title(self.get_title())
            builder.add_raw_rst(".. contents:: Topics\n")

            if self.changes.ancestor and self.config.mention_ancestor:
                builder.add_raw_rst(
                    "This changelog describes changes after version {0}.\n".format(
                        self.changes.ancestor
                    )
                )
            else:
                builder.add_raw_rst("")

        self.generate_to(builder, 0, only_latest=only_latest)

        return builder.generate()

    def _add_section(
        self,
        builder: RstBuilder,
        changelog_entry: ChangelogEntry,
        section_name: str,
        start_level: int,
    ) -> None:
        """
        Add a section of fragments to the changelog.
        """
        if section_name not in changelog_entry.changes:
            return

        section_title = self.config.sections[section_name]
        builder.add_section(section_title, start_level + 1)

        changelog_entry.add_section_content(builder, section_name)

        builder.add_raw_rst("")

    @staticmethod
    def _add_plugins(
        builder: RstBuilder,
        plugins_database: dict[str, list[dict[str, Any]]],
        fqcn_prefix: str | None,
        start_level: int = 0,
    ) -> None:
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
                builder.add_section("New Plugins", start_level + 1)

            builder.add_section(plugin_type.title(), start_level + 2)

            ChangelogGenerator.add_plugins(builder, plugins, fqcn_prefix)

            builder.add_raw_rst("")

    @staticmethod
    def add_plugins(
        builder: RstBuilder, plugins: list[dict[str, Any]], fqcn_prefix: str | None
    ) -> None:
        """
        Add new plugins of one type to the changelog.
        """
        for plugin in sorted(plugins, key=lambda plugin: plugin["name"]):
            plugin_name = get_plugin_name(plugin["name"], fqcn_prefix=fqcn_prefix)
            builder.add_raw_rst("- %s - %s" % (plugin_name, plugin["description"]))

    @staticmethod
    def _add_modules(
        builder: RstBuilder,
        modules: list[dict[str, Any]],
        flatmap: bool,
        fqcn_prefix: str | None,
        start_level: int = 0,
    ) -> None:
        """
        Add new modules to the changelog.
        """
        if not modules:
            return

        builder.add_section("New Modules", start_level + 1)
        ChangelogGenerator.add_modules(
            builder, modules, flatmap, fqcn_prefix, start_level + 2
        )

    @staticmethod
    def add_modules(
        builder: RstBuilder,
        modules: list[dict[str, Any]],
        flatmap: bool,
        fqcn_prefix: str | None,
        level: int,
    ) -> None:
        """
        Add new modules to the changelog.
        """
        modules_by_namespace = collections.defaultdict(list)
        for module in sorted(modules, key=lambda module: module["name"]):
            modules_by_namespace[module["namespace"]].append(module)

        previous_section = None
        for namespace in sorted(modules_by_namespace):
            parts = namespace.split(".")

            section = parts.pop(0).replace("_", " ").title()

            if section != previous_section and section:
                builder.add_section(section, level)

            previous_section = section

            subsection = ".".join(parts)

            if subsection:
                builder.add_section(subsection, level + 1)

            for module in modules_by_namespace[namespace]:
                module_name = get_plugin_name(
                    module["name"],
                    fqcn_prefix=fqcn_prefix,
                    namespace=namespace,
                    flatmap=flatmap,
                )
                builder.add_raw_rst("- %s - %s" % (module_name, module["description"]))

            builder.add_raw_rst("")

    @staticmethod
    def _add_objects(
        builder: RstBuilder,
        objects_database: dict[str, list[dict[str, Any]]],
        fqcn_prefix: str | None,
        start_level: int = 0,
    ) -> None:
        """
        Add new objects to the changelog.
        """
        if not objects_database:
            return

        for object_type in sorted(objects_database):
            objects = objects_database.get(object_type)
            if not objects:
                continue

            builder.add_section("New " + object_type.title() + "s", start_level + 1)

            ChangelogGenerator.add_objects(builder, objects, fqcn_prefix)

            builder.add_raw_rst("")

    @staticmethod
    def add_objects(
        builder: RstBuilder, objects: list[dict[str, Any]], fqcn_prefix: str | None
    ) -> None:
        """
        Add new objects of one type to the changelog.
        """
        for ansible_object in sorted(
            objects, key=lambda ansible_object: ansible_object["name"]
        ):
            object_name = get_plugin_name(
                ansible_object["name"], fqcn_prefix=fqcn_prefix
            )
            builder.add_raw_rst(
                "- %s - %s" % (object_name, ansible_object["description"])
            )


def generate_changelog(  # pylint: disable=too-many-arguments
    paths: PathsConfig,
    config: ChangelogConfig,
    changes: ChangesBase,
    plugins: list[PluginDescription] | None = None,
    fragments: list[ChangelogFragment] | None = None,
    flatmap: bool = True,
    changelog_path: str | None = None,
    only_latest: bool = False,
):
    """
    Generate the changelog as reStructuredText.

    :arg plugins: Will be loaded if necessary. Only provide when you already have them
    :arg fragments: Will be loaded if necessary. Only provide when you already have them
    :arg flatmap: Whether the collection uses flatmapping or not
    :arg changelog_path: Write the output to this path instead of the default path.
    :arg only_latest: Only write the last changelog entry without any preamble
    """
    if changelog_path is None:
        major_minor_version = ".".join(
            changes.latest_version.split(".")[: config.changelog_filename_version_depth]
        )
        if "%s" in config.changelog_filename_template:
            changelog_filename = config.changelog_filename_template % (
                major_minor_version,
            )
        else:
            changelog_filename = config.changelog_filename_template
        changelog_path = os.path.join(paths.changelog_dir, changelog_filename)

    generator = ChangelogGenerator(config, changes, plugins, fragments, flatmap)
    rst = generator.generate(only_latest=only_latest)

    with open(changelog_path, "wb") as changelog_fd:
        changelog_fd.write(rst.encode("utf-8"))

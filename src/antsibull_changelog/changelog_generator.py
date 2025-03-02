# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Generate reStructuredText changelog from ChangesData instance.
"""

from __future__ import annotations

import abc
import collections
from collections.abc import MutableMapping
from typing import Any, cast

from .changes import ChangesData, FragmentResolver, PluginResolver
from .config import ChangelogConfig, ChangelogRenderConfig, TextFormat
from .logger import LOGGER
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
    changes: ChangesData
    plugin_resolver: PluginResolver
    fragment_resolver: FragmentResolver
    render_config: ChangelogRenderConfig

    def __init__(
        self,
        config: ChangelogConfig,
        changes: ChangesData,
        *,
        flatmap: bool = True,
        render_config: ChangelogRenderConfig | None = None,
    ):
        """
        Create a changelog generator.
        """
        self.config = config
        self.changes = changes
        self.flatmap = flatmap
        if render_config is None:
            render_config = ChangelogRenderConfig()
        self.render_config = render_config

        self.plugin_resolver = changes.get_plugin_resolver()
        self.object_resolver = changes.get_object_resolver()
        self.fragment_resolver = changes.get_fragment_resolver()

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
            latest_version.split(".")[: self.render_config.title_version_depth]
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

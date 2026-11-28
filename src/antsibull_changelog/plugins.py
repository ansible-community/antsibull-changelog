# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Collect and store information on Ansible plugins and modules.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from antsibull_docs_loader.ansible import (
    ALL_DOCUMENTABLE_PLUGIN_TYPES,
    CORE_DOCUMENTABLE_PLUGIN_TYPES,
)
from antsibull_docs_loader.data import CollectionInfo
from antsibull_docs_loader.loader import (
    Documentation,
    load_docs,
    load_docs_from_role_argspec_file,
)
from antsibull_docs_loader.routing import (
    CollectionRouting,
    File,
    complete_redirects_for_collection,
    load_routing_information,
)
from antsibull_docs_parser import dom as _ansible_markup_dom
from antsibull_docs_parser.parser import Context as _AnsibleMarkupContext
from antsibull_docs_parser.parser import Whitespace as _AnsibleMarkupWhitespace
from antsibull_docs_parser.parser import parse as _parse_ansible_markup
from antsibull_docs_parser.rst import (
    PlainRSTFormatter as _AnsibleMarkupRSTFormatterBase,
)
from antsibull_docs_parser.rst import rst_escape as _ansible_markup_rst_escape
from antsibull_docs_parser.rst import to_rst_plain as _ansible_markup_to_rst
from antsibull_fileutils.yaml import load_yaml_file, store_yaml_file

from .ansible import (
    OBJECT_TYPES,
)
from .config import ChangelogConfig, CollectionDetails, PathsConfig
from .logger import LOGGER


class _AnsibleMarkupRSTFormatter(_AnsibleMarkupRSTFormatterBase):
    @staticmethod
    def _format_option_like(
        part: _ansible_markup_dom.OptionNamePart | _ansible_markup_dom.ReturnValuePart,
    ) -> str:
        value_text = part.name
        value = part.value
        if value is not None:
            value_text = f"{value_text}={value}"
        escaped_text = _ansible_markup_rst_escape(
            value_text, escape_ending_whitespace=True, must_not_be_empty=True
        )
        return f"\\ :literal:`{escaped_text}`\\ "

    def format_module(
        self, part: _ansible_markup_dom.ModulePart, url: str | None
    ) -> str:
        return _ansible_markup_rst_escape(part.fqcn)

    def format_option_name(
        self, part: _ansible_markup_dom.OptionNamePart, url: str | None
    ) -> str:
        return self._format_option_like(part)

    def format_plugin(
        self, part: _ansible_markup_dom.PluginPart, url: str | None
    ) -> str:
        return _ansible_markup_rst_escape(part.plugin.fqcn)

    def format_return_value(
        self, part: _ansible_markup_dom.ReturnValuePart, url: str | None
    ) -> str:
        return self._format_option_like(part)


class PluginDescription:
    # pylint: disable=too-few-public-methods
    """
    Stores a description of one plugin.
    """

    category: str
    type: str
    name: str
    namespace: str | None
    description: str
    version_added: str | None

    def __init__(
        self,
        plugin_type: str,
        name: str,
        namespace: str | None,
        description: str,
        version_added: str | None,
        category: str = "plugin",
    ):
        # pylint: disable=too-many-arguments
        """
        Create a new plugin description.
        """
        self.category = category
        self.type = plugin_type
        self.name = name
        self.namespace = namespace
        self.description = description
        self.version_added = version_added

    @staticmethod
    def from_dict(
        data: dict[str, dict[str, dict[str, Any]]],
        category: str = "plugin",
        add_plugin_period: bool = False,
    ) -> list[PluginDescription]:
        """
        Return a list of ``PluginDescription`` objects from the given data.

        :arg data: A dictionary mapping plugin types to a dictionary of plugins.
        :return: A list of plugin descriptions.
        """
        plugins = []

        for plugin_type, plugin_data in data.items():
            for plugin_name, plugin_details in plugin_data.items():
                description = plugin_details["description"]
                if (
                    add_plugin_period
                    and description
                    and not description.endswith((".", ",", "!", "?"))
                ):
                    description += "."
                # Process Ansible markup
                try:
                    markup = _parse_ansible_markup(
                        description or "",
                        _AnsibleMarkupContext(),
                        errors="exception",
                        whitespace=_AnsibleMarkupWhitespace.STRIP,
                    )
                    description = _ansible_markup_to_rst(
                        markup, formatter=_AnsibleMarkupRSTFormatter()
                    )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    LOGGER.warning(
                        "Error while parsing description of {0} {1}: {2}",
                        plugin_type,
                        plugin_name,
                        str(exc),
                    )
                plugins.append(
                    PluginDescription(
                        plugin_type=plugin_type,
                        name=plugin_name,
                        namespace=plugin_details.get("namespace"),
                        description=description,
                        version_added=plugin_details["version_added"],
                        category=category,
                    )
                )

        return plugins


def _remove_empty_namespaces(plugins_data: dict[str, Any]) -> None:
    # remove empty namespaces from plugins
    for category in ("plugins", "objects"):
        for section in plugins_data[category].values():
            for plugin in section.values():
                if plugin["namespace"] is None:
                    del plugin["namespace"]


def _get_collection_info(
    paths: PathsConfig,
    collection_details: CollectionDetails,
) -> CollectionInfo:
    if paths.is_collection:
        namespace = collection_details.get_namespace()
        name = collection_details.get_name()
        return CollectionInfo(
            path=Path(paths.base_dir),
            namespace=namespace,
            name=name,
            full_name=f"{namespace}.{name}",
            version=collection_details.version,
            is_ansible_core=False,
        )
    return CollectionInfo(
        path=Path(paths.base_dir) / "lib" / "ansible",
        namespace="ansible",
        name="builtin",
        full_name="ansible.builtin",
        version=None,  # we don't need the correct value
        is_ansible_core=True,
    )


def _get_entry(
    plugin_fqcn: tuple[str, ...], plugin_type: str, docs: Documentation | None
) -> tuple[str, dict[str, Any]]:
    description = docs.documentation.get("short_description") if docs else None
    version_added = docs.documentation.get("version_added") if docs else None
    if plugin_type == "module":
        return plugin_fqcn[-1], {
            "name": plugin_fqcn[-1],
            "namespace": ".".join(plugin_fqcn[:-1]),
            "description": description,
            "version_added": version_added,
        }
    fqcn = ".".join(plugin_fqcn)
    return fqcn, {
        "name": fqcn,
        "namespace": None,
        "description": description,
        "version_added": version_added,
    }


def _resolve(
    *,
    collection_name: str,
    routing_info: CollectionRouting,
    plugin_fqcn: tuple[str, ...],
    plugin_type: str,
    plugin_file: File,
) -> File | None:
    if plugin_type not in routing_info.plugin_data:
        return plugin_file
    routing = routing_info.plugin_data[plugin_type].get(".".join(plugin_fqcn))
    if routing is None or routing.redirect is None:
        return plugin_file
    if routing.redirect is ...:
        return None
    if not routing.redirect.startswith(f"{collection_name}."):
        return None
    new_fqcn = tuple(routing.redirect[len(collection_name) + 1 :].split("."))
    return routing_info.files[plugin_type].get(new_fqcn)


def _refresh_plugin_cache(  # pylint: disable=too-many-locals
    paths: PathsConfig,
    collection_details: CollectionDetails,
    version: str,
) -> dict[str, Any]:
    LOGGER.info("refreshing plugin cache")
    plugins_data: dict[str, Any] = {
        "version": version,
        "plugins": {},
        "objects": {},
    }

    collection_info = _get_collection_info(paths, collection_details)
    routing_info = load_routing_information(collection_info)
    complete_redirects_for_collection(
        {collection_info.full_name: routing_info},
        collection_name=collection_info.full_name,
    )
    for plugin_type in ALL_DOCUMENTABLE_PLUGIN_TYPES:
        if (
            not paths.is_collection
            and plugin_type not in CORE_DOCUMENTABLE_PLUGIN_TYPES
        ):
            continue
        dest: dict[str, dict[str, str | None]] = {}
        destination = (
            plugins_data["objects"]
            if plugin_type in OBJECT_TYPES
            else plugins_data["plugins"]
        )
        destination[plugin_type] = dest
        plugin_data = routing_info.files.get(plugin_type)
        if plugin_data is None:
            continue
        for plugin_fqcn, plugin_file in sorted(plugin_data.items()):
            actual_plugin_file = _resolve(
                collection_name=collection_info.full_name,
                routing_info=routing_info,
                plugin_fqcn=plugin_fqcn,
                plugin_type=plugin_type,
                plugin_file=plugin_file,
            )
            if actual_plugin_file is None:
                continue
            if plugin_type == "role":
                entrypoints = load_docs_from_role_argspec_file(
                    actual_plugin_file.docs_candidates[0]
                )
                if entrypoints is not None:
                    fqcn, entry = _get_entry(
                        plugin_fqcn, plugin_type, entrypoints.entrypoints.get("main")
                    )
                    dest[fqcn] = entry
            else:
                docs_path = load_docs(actual_plugin_file.docs_candidates)
                if docs_path is not None:
                    fqcn, entry = _get_entry(plugin_fqcn, plugin_type, docs_path[0])
                    dest[fqcn] = entry

    _remove_empty_namespaces(plugins_data)
    return plugins_data


def load_plugins(  # pylint: disable=too-many-arguments
    paths: PathsConfig,
    collection_details: CollectionDetails,
    # pylint: disable-next=unused-argument
    config: ChangelogConfig,
    version: str,
    force_reload: bool = False,
    # pylint: disable-next=unused-argument,fixme
    use_ansible_doc: bool = False,  # TODO: add runtime deprecation!
    add_plugin_period: bool = False,
    *,
    ignore_cache: bool = False,
) -> list[PluginDescription]:
    """
    Load plugins from ansible-doc.

    :arg paths: Paths configuration
    :arg collection_details: Collection details
    :arg version: The current version. Used for caching data
    :arg force_reload: Set to ``True`` to ignore potentially cached data
    :arg ignore_cache: Set to ``True`` to neither read nor write the cache.
        Implies ``force_reload=True``.
    :return: A list of all plugins
    """
    if paths.is_other_project:
        return []

    plugin_cache_path = os.path.join(paths.changelog_dir, ".plugin-cache.yaml")
    plugins_data: dict[str, Any] = {}

    if not ignore_cache and not force_reload and os.path.exists(plugin_cache_path):
        plugins_data = load_yaml_file(plugin_cache_path)
        if version != plugins_data["version"]:
            LOGGER.info(
                "version {} does not match plugin cache version {}",
                version,
                plugins_data["version"],
            )
            plugins_data = {}

    if not plugins_data:
        plugins_data = _refresh_plugin_cache(
            paths,
            collection_details,
            version,
        )
        if not ignore_cache:
            store_yaml_file(plugin_cache_path, plugins_data)

    plugins = PluginDescription.from_dict(
        plugins_data["plugins"],
        add_plugin_period=add_plugin_period,
    )
    if "objects" in plugins_data:
        plugins.extend(
            PluginDescription.from_dict(
                plugins_data["objects"],
                category="object",
                add_plugin_period=add_plugin_period,
            )
        )

    return plugins

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

import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Literal

from antsibull_docs_loader.ansible import (
    ALL_DOCUMENTABLE_PLUGIN_TYPES,
    CORE_DOCUMENTABLE_PLUGIN_TYPES,
    EDA_PLUGIN_TYPES,
)
from antsibull_docs_loader.data import CollectionInfo
from antsibull_docs_loader.loader import (
    Documentation,
    load_docs,
    load_docs_from_role_argspec_file,
)
from antsibull_docs_loader.routing import load_routing_information
from antsibull_docs_parser import dom as _ansible_markup_dom
from antsibull_docs_parser.parser import Context as _AnsibleMarkupContext
from antsibull_docs_parser.parser import Whitespace as _AnsibleMarkupWhitespace
from antsibull_docs_parser.parser import parse as _parse_ansible_markup
from antsibull_docs_parser.rst import (
    PlainRSTFormatter as _AnsibleMarkupRSTFormatterBase,
)
from antsibull_docs_parser.rst import rst_escape as _ansible_markup_rst_escape
from antsibull_docs_parser.rst import to_rst_plain as _ansible_markup_to_rst
from antsibull_fileutils.copier import CollectionCopier, Copier, GitCopier
from antsibull_fileutils.vcs import detect_vcs
from antsibull_fileutils.yaml import load_yaml_file, store_yaml_file

from .ansible import (
    OBJECT_TYPES,
    PLUGIN_EXCEPTIONS,
    get_documentable_objects,
    get_documentable_plugins,
)
from .config import ChangelogConfig, CollectionDetails, PathsConfig
from .logger import LOGGER

PluginMode = Literal["compare", "old", "new"]

_FAIL_ON_BAD_COMPARISON = False


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


def extract_namespace(
    paths: PathsConfig, collection_name: str | None, filename: str
) -> str:
    """
    Given a filename of a module, will extract the module's namespace.
    """
    # Follow links
    filename = os.path.realpath(filename)
    # Determine relative path
    if collection_name:
        rel_to = os.path.join(paths.base_dir, "plugins", "modules")
    else:
        rel_to = os.path.join(paths.base_dir, "lib", "ansible", "modules")
    path = os.path.relpath(filename, rel_to)
    path = os.path.split(path)[0]
    # Extract namespace from relative path
    namespace_list: list[str] = []
    while True:
        (path, last), prev = os.path.split(path), path
        if path == prev:
            break
        if last not in ("", ".", ".."):
            namespace_list.insert(0, last)
    return ".".join(namespace_list)


def jsondoc_to_metadata(  # pylint: disable=too-many-arguments
    paths: PathsConfig,
    collection_name: str | None,
    plugin_type: str,
    name: str,
    data: dict[str, Any],
    category: str = "plugin",
    is_ansible_core_2_13: bool = False,
) -> dict[str, Any]:
    """
    Convert ``ansible-doc --json`` output to plugin metadata.

    :arg paths: Paths configuration
    :arg collection_name: The name of the collection, if appropriate
    :arg plugin_type: The plugin's or object's type
    :arg name: The plugin's name
    :arg data: The JSON for this plugin returned by ``ansible-doc --json``
    :arg category: Set to ``object`` for roles and playbooks
    :arg is_ansible_core_2_13: Set to ``True`` for ``--metadata-dump`` output
    """
    namespace: str | None = None
    if collection_name and name.startswith(collection_name + "."):
        name = name[len(collection_name) + 1 :]
    docs: dict = data.get("doc") or {}
    if category == "object" and plugin_type == "role":
        entrypoints: dict = data.get("entry_points") or {}
        if "main" in entrypoints:
            docs = entrypoints["main"]
    if category == "plugin" and plugin_type == "module":
        if is_ansible_core_2_13:
            last_dot = name.rfind(".")
            if last_dot >= 0:
                namespace = name[:last_dot]
                name = name[last_dot + 1 :]
            else:
                namespace = ""
        else:
            filename: str | None = docs.get("filename")
            if filename:
                namespace = extract_namespace(paths, collection_name, filename)
            if "." in name:
                # Flatmapping
                name = name[name.rfind(".") + 1 :]
    return {
        "description": docs.get("short_description"),
        "name": name,
        "namespace": namespace,
        "version_added": docs.get("version_added"),
    }


def get_plugins_path(
    paths: PathsConfig, plugin_type: str, category: str = "plugin"
) -> str:
    """
    Return path to plugins of a given type.
    """
    if paths.is_collection:
        if category == "object":
            return os.path.join(paths.base_dir, "{0}s".format(plugin_type))
        return os.path.join(
            paths.base_dir,
            "plugins",
            "modules" if plugin_type == "module" else plugin_type,
        )
    lib_ansible = os.path.join(paths.base_dir, "lib", "ansible")
    if plugin_type == "module":
        return os.path.join(lib_ansible, "modules")
    return os.path.join(lib_ansible, "plugins", plugin_type)


def list_plugins_walk(
    paths: PathsConfig,
    playbook_dir: str | None,  # pylint: disable=unused-argument
    plugin_type: str,
    collection_name: str | None,
) -> list[str]:
    """
    Find all plugins of a type in a collection, or in ansible-core/-base. Uses os.walk().

    This will also work with Ansible 2.9.

    :arg paths: Paths configuration
    :arg playbook_dir: Value for the ``--playbook-dir`` argument of ``ansible-doc``
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate.
    """
    plugin_source_path = get_plugins_path(paths, plugin_type)

    if not os.path.exists(plugin_source_path):
        return []

    plugin_source_path = os.path.realpath(plugin_source_path)

    result = set()
    for dirpath, _, filenames in os.walk(plugin_source_path):
        if plugin_type != "module" and dirpath != plugin_source_path:
            continue
        for filename in filenames:
            if filename == "__init__.py" or not filename.endswith(".py"):
                continue
            if not paths.is_collection and dirpath == plugin_source_path:
                # Skip files which are *not* plugins/modules, but live in these directories inside
                # ansible-core/-base.
                if (plugin_type, filename) in PLUGIN_EXCEPTIONS:
                    continue
            path = os.path.realpath(os.path.join(dirpath, filename))
            path = os.path.splitext(path)[0]
            relpath = os.path.relpath(path, plugin_source_path)
            if not paths.is_collection and os.sep in relpath:
                # When listing modules in ansible-core/-base, get rid of the namespace.
                relpath = os.path.basename(relpath)
            relname = relpath.replace(os.sep, ".")
            if collection_name:
                relname = "{0}.{1}".format(collection_name, relname)
            result.add(relname)

    return sorted(result)


def _check_output(command: list[str]) -> bytes:
    return subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def list_plugins_ansibledoc(
    paths: PathsConfig,
    playbook_dir: str | None,
    plugin_type: str,
    collection_name: str | None,
    category: str = "plugin",
) -> list[str]:
    """
    Find all plugins of a type in a collection, or in ansible-core/-base. Uses ansible-doc.

    Note that ansible-doc from Ansible 2.10 or newer is needed for this!

    :arg paths: Paths configuration
    :arg playbook_dir: Value for the ``--playbook-dir`` argument of ``ansible-doc``
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate.
    """
    plugin_source_path = get_plugins_path(paths, plugin_type, category)

    if not os.path.exists(plugin_source_path) or os.listdir(plugin_source_path) == []:
        return []

    command = [paths.ansible_doc_path, "--json", "-t", plugin_type, "--list"]
    if playbook_dir:
        command.extend(["--playbook-dir", playbook_dir])
    if collection_name:
        command.append(collection_name)
    output = _check_output(command)
    plugins_list = json.loads(output.decode("utf-8"))

    if not collection_name:
        # Filter out FQCNs
        plugins_list = {
            name: data
            for name, data in plugins_list.items()
            if "." not in name or name.startswith("ansible.builtin.")
        }
    else:
        # Filter out without / wrong FQCN
        plugins_list = {
            name: data
            for name, data in plugins_list.items()
            if name.startswith(collection_name + ".")
        }

    return sorted(plugins_list.keys())


def run_ansible_doc(
    paths: PathsConfig,
    playbook_dir: str | None,
    plugin_type: str,
    plugin_names: list[str],
) -> dict:
    """
    Runs ansible-doc to retrieve documentation for a given set of plugins in JSON format.

    Plugins must be in FQCN for collections.
    """
    command = [paths.ansible_doc_path, "--json", "-t", plugin_type]
    if playbook_dir:
        command.extend(["--playbook-dir", playbook_dir])
    command.extend(plugin_names)
    output = _check_output(command)
    return json.loads(output.decode("utf-8"))


def run_ansible_doc_metadata_dump(
    paths: PathsConfig, playbook_dir: str | None, collection_name: str
) -> dict:
    """
    Runs ansible-doc to retrieve documentation for all plugins in a collection.
    """
    command = [paths.ansible_doc_path, "--metadata-dump", collection_name]
    if playbook_dir:
        command.extend(["--playbook-dir", playbook_dir])
    output = _check_output(command)
    return json.loads(output.decode("utf-8"))


def _load_plugins_2_13(
    plugins_data: dict[str, Any],
    paths: PathsConfig,
    collection_name: str,
    playbook_dir: str | None = None,
) -> None:
    LOGGER.debug("Run ansible-doc for {!r}", playbook_dir)
    data = run_ansible_doc_metadata_dump(paths, playbook_dir, collection_name)["all"]

    LOGGER.debug("Processing result")
    for category, category_types in (
        ("plugins", get_documentable_plugins()),
        ("objects", get_documentable_objects()),
    ):
        for plugin_type in category_types:
            if plugin_type in data:
                plugins_data[category][plugin_type] = {}
                for plugin_name, plugin_data in data[plugin_type].items():
                    if plugin_name.startswith("ansible.builtin._"):
                        plugin_name = plugin_name.replace("_", "", 1)
                    processed_data = jsondoc_to_metadata(
                        paths,
                        collection_name,
                        plugin_type,
                        plugin_name,
                        plugin_data,
                        category=category[:-1],
                        is_ansible_core_2_13=True,
                    )
                    plugins_data[category][plugin_type][
                        processed_data["name"]
                    ] = processed_data


@contextmanager
def collection_copier(
    paths: PathsConfig, config: ChangelogConfig, namespace: str, name: str
) -> Generator[tuple[str, PathsConfig], None, None]:
    """
    Creates a copy of a collection to a place where ``--playbook-dir`` can be used
    to prefer this copy of the collection over any installed ones.
    """
    vcs = config.vcs
    if vcs == "auto":
        vcs = detect_vcs(paths.base_dir, log_debug=LOGGER.debug)
    copier = {
        "none": Copier,
        "git": GitCopier,
    }[
        vcs
    ](log_debug=LOGGER.debug)

    with CollectionCopier(
        source_directory=paths.base_dir,
        namespace=namespace,
        name=name,
        copier=copier,
        log_debug=LOGGER.debug,
    ) as (root_dir, collection_dir):
        new_paths = PathsConfig.force_collection(
            collection_dir, ansible_doc_bin=paths.ansible_doc_path
        )
        yield root_dir, new_paths


def _load_collection_plugins_2_13(
    plugins_data: dict[str, Any],
    paths: PathsConfig,
    collection_details: CollectionDetails,
    config: ChangelogConfig,
) -> None:
    collection_name = "{}.{}".format(
        collection_details.get_namespace(), collection_details.get_name()
    )

    with collection_copier(
        paths, config, collection_details.get_namespace(), collection_details.get_name()
    ) as (playbook_dir, new_paths):
        _load_plugins_2_13(
            plugins_data, new_paths, collection_name, playbook_dir=playbook_dir
        )


def _remove_empty_namespaces(plugins_data: dict[str, Any]) -> None:
    # remove empty namespaces from plugins
    for category in ("plugins", "objects"):
        for section in plugins_data[category].values():
            for plugin in section.values():
                if plugin["namespace"] is None:
                    del plugin["namespace"]


def _refresh_plugin_cache(
    paths: PathsConfig,
    collection_details: CollectionDetails,
    config: ChangelogConfig,
    version: str,
) -> dict[str, Any]:
    LOGGER.info("refreshing plugin cache")
    plugins_data: dict[str, Any] = {
        "version": version,
        "plugins": {},
        "objects": {},
    }

    if paths.is_collection:
        _load_collection_plugins_2_13(plugins_data, paths, collection_details, config)
    else:
        _load_plugins_2_13(plugins_data, paths, "ansible.builtin")

    _remove_empty_namespaces(plugins_data)
    return plugins_data


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


def _refresh_plugin_cache_new(  # pylint: disable=too-many-locals
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
            if plugin_type == "role":
                entrypoints = load_docs_from_role_argspec_file(
                    plugin_file.docs_candidates[0]
                )
                if entrypoints is not None:
                    fqcn, entry = _get_entry(
                        plugin_fqcn, plugin_type, entrypoints.entrypoints.get("main")
                    )
                    dest[fqcn] = entry
            else:
                docs = load_docs(plugin_file.docs_candidates)
                if docs is not None:
                    fqcn, entry = _get_entry(plugin_fqcn, plugin_type, docs)
                    dest[fqcn] = entry

    _remove_empty_namespaces(plugins_data)
    return plugins_data


_ISSUES_URL = "https://github.com/ansible-community/antsibull-changelog/issues/"
_COMPARE_MESSAGE = f"Please report this issue in {_ISSUES_URL}. Thanks!"


def _compare_plugin_type(
    *,
    category: str,
    plugin_type: str,
    op: dict[str, Any],
    np: dict[str, Any],
    is_ansible_core: bool,
) -> None:
    if sorted(op) != sorted(np):
        missing = sorted(set(op) - set(np))
        superfluous = sorted(set(np) - set(op))
        if is_ansible_core and plugin_type in ("filter", "test"):
            # Ansible-core includes docs for builtin Jinja2 filters and tests.
            # antsibull-docs-loader doesn't know about these yet and will not return them.
            # Since they never have 'version_added', this doesn't matter for our use-case,
            # so we don't warn about them.
            missing.clear()
        if missing or superfluous:
            LOGGER.warning(
                f"Found differences when scanning plugin cache for {category}.{plugin_type}:"
                f" missing {missing}, superfluous {superfluous}. {_COMPARE_MESSAGE}",
                missing=missing,
                superfluous=superfluous,
            )
            if _FAIL_ON_BAD_COMPARISON:
                raise ValueError("Comparison failed!")
    for plugin_name in op:
        if plugin_name in np:
            opd = op[plugin_name]
            npd = np[plugin_name]
            if opd != npd:
                LOGGER.warning(
                    "Found differences when scanning plugin cache for"
                    f" {category}.{plugin_type}.{plugin_name}: {{opd}} vs. {{npd}}."
                    f" {_COMPARE_MESSAGE}",
                    opd=opd,
                    npd=npd,
                )
                if _FAIL_ON_BAD_COMPARISON:
                    raise ValueError("Comparison failed!")


def _refresh_plugin_cache_cmp(
    paths: PathsConfig,
    collection_details: CollectionDetails,
    config: ChangelogConfig,
    version: str,
    plugin_mode: PluginMode,
) -> dict[str, Any]:
    if plugin_mode == "old":
        return _refresh_plugin_cache(paths, collection_details, config, version)
    if plugin_mode == "new":
        return _refresh_plugin_cache_new(paths, collection_details, version)
    old_cache = _refresh_plugin_cache(paths, collection_details, config, version)
    new_cache = _refresh_plugin_cache_new(paths, collection_details, version)
    for category in ("plugins", "objects"):
        # Skip EDA plugin types since the old method does not support them
        o = [pt for pt in old_cache[category] if pt not in EDA_PLUGIN_TYPES]
        n = [pt for pt in new_cache[category] if pt not in EDA_PLUGIN_TYPES]
        if sorted(o) != sorted(n):
            LOGGER.warning(
                f"Found differences when scanning plugin cache for {category}:"
                f" missing {{missing}}, superfluous {{superfluous}}. {_COMPARE_MESSAGE}",
                missing=sorted(set(o) - set(n)),
                superfluous=sorted(set(n) - set(o)),
            )
            if _FAIL_ON_BAD_COMPARISON:
                raise ValueError("Comparison failed!")
        for plugin_type in o:
            if plugin_type in n:
                _compare_plugin_type(
                    category=category,
                    plugin_type=plugin_type,
                    op=old_cache[category][plugin_type],
                    np=new_cache[category][plugin_type],
                    is_ansible_core=not paths.is_collection,
                )
    return new_cache


def load_plugins(  # pylint: disable=too-many-arguments
    paths: PathsConfig,
    collection_details: CollectionDetails,
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

    # pylint: disable-next=fixme
    # TODO: change to 'new' in next version
    plugin_mode: PluginMode = "compare"

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
        plugins_data = _refresh_plugin_cache_cmp(
            paths,
            collection_details,
            config,
            version,
            plugin_mode=plugin_mode,
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

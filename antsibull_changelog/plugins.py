# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Collect and store information on Ansible plugins and modules.
"""

import json
import os
import subprocess

from typing import Any, Dict, List, Optional

from .ansible import get_documentable_plugins
from .config import CollectionDetails, PathsConfig
from .logger import LOGGER
from .yaml import load_yaml, store_yaml


class PluginDescription:
    # pylint: disable=too-few-public-methods
    """
    Stores a description of one plugin.
    """

    type: str
    name: str
    namespace: Optional[str]
    description: str
    version_added: Optional[str]

    def __init__(self, plugin_type: str, name: str, namespace: Optional[str],
                 description: str, version_added: Optional[str]):
        # pylint: disable=too-many-arguments
        """
        Create a new plugin description.
        """
        self.type = plugin_type
        self.name = name
        self.namespace = namespace
        self.description = description
        self.version_added = version_added

    @staticmethod
    def from_dict(data: Dict[str, Dict[str, Dict[str, Any]]]):
        """
        Return a list of ``PluginDescription`` objects from the given data.

        :arg data: A dictionary mapping plugin types to a dictionary of plugins.
        :return: A list of plugin descriptions.
        """
        plugins = []

        for plugin_type, plugin_data in data.items():
            for plugin_name, plugin_details in plugin_data.items():
                plugins.append(PluginDescription(
                    plugin_type=plugin_type,
                    name=plugin_name,
                    namespace=plugin_details.get('namespace'),
                    description=plugin_details['description'],
                    version_added=plugin_details['version_added'],
                ))

        return plugins


def follow_links(path: str) -> str:
    """
    Given a path, will recursively resolve symbolic links.
    """
    tried_links = set()
    while os.path.islink(path):
        if path in tried_links:
            raise Exception(
                'Found infinite symbolic link loop involving "{0}"'.format(path))
        tried_links.add(path)
        path = os.path.normpath(os.path.join(os.path.dirname(path), os.readlink(path)))
    return path


def jsondoc_to_metadata(paths: PathsConfig, collection_name: Optional[str],
                        plugin_type: str, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ``ansible-doc --json`` output to plugin metadata.

    :arg paths: Paths configuration
    :arg collection_name: The name of the collection, if appropriate
    :arg plugin_type: The plugin's type
    :arg name: The plugin's name
    :arg data: The JSON for this plugin returned by ``ansible-doc --json``
    """
    namespace: Optional[str] = None
    if collection_name and name.startswith(collection_name + '.'):
        name = name[len(collection_name) + 1:]
    docs: dict = data.get('doc') or dict()
    if plugin_type == 'module':
        filename: Optional[str] = docs.get('filename')
        if filename:
            # Follow links
            filename = follow_links(filename)
            # Determine relative path
            if collection_name:
                rel_to = os.path.join(paths.base_dir, 'plugins', 'modules')
            else:
                rel_to = os.path.join(paths.base_dir, 'lib', 'ansible', 'modules')
            path = os.path.relpath(filename, rel_to)
            path = os.path.split(path)[0]
            # Extract namespace from relative path
            namespace_list: List[str] = []
            while True:
                (path, last), prev = os.path.split(path), path
                if path == prev:
                    break
                if last not in ('', '.', '..'):
                    namespace_list.insert(0, last)
            namespace = '.'.join(namespace_list)
        if '.' in name:
            # Flatmapping
            name = name[name.rfind('.') + 1:]
    return {
        'description': docs.get('short_description'),
        'name': name,
        'namespace': namespace,
        'version_added': docs.get('version_added'),
    }


def get_plugins_path(paths: PathsConfig, plugin_type: str) -> str:
    """
    Return path to plugins of a given type.
    """
    if paths.is_collection:
        return os.path.join(
            paths.base_dir, 'plugins', 'modules' if plugin_type == 'module' else plugin_type)
    lib_ansible = os.path.join(paths.base_dir, 'lib', 'ansible')
    if plugin_type == 'module':
        return os.path.join(lib_ansible, 'modules')
    return os.path.join(lib_ansible, 'plugins', plugin_type)


def list_plugins_walk(paths: PathsConfig, plugin_type: str,
                      collection_name: Optional[str]) -> List[str]:
    """
    Find all plugins of a type in a collection, or in Ansible-base. Uses os.walk().

    This will also work with Ansible 2.9.

    :arg paths: Paths configuration
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate.
    """
    plugin_source_path = get_plugins_path(paths, plugin_type)

    if not os.path.exists(plugin_source_path):
        return []

    result = set()
    for dirpath, _, filenames in os.walk(plugin_source_path):
        if plugin_type != 'module' and dirpath != plugin_source_path:
            continue
        for filename in filenames:
            if filename == '__init__.py' or not filename.endswith('.py'):
                continue
            path = follow_links(os.path.join(dirpath, filename))
            if path.endswith('.py'):
                path = path[:-len('.py')]
            relpath = os.path.relpath(path, plugin_source_path)
            relname = relpath.replace(os.sep, '.')
            if collection_name:
                relname = '{0}.{1}'.format(collection_name, relname)
            result.add(relname)

    return sorted(result)


def list_plugins_ansibledoc(paths: PathsConfig, plugin_type: str,
                            collection_name: Optional[str]) -> List[str]:
    """
    Find all plugins of a type in a collection, or in Ansible-base. Uses ansible-doc.

    Note that ansible-doc from Ansible 2.10 or newer is needed for this!

    :arg paths: Paths configuration
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate.
    """
    plugin_source_path = get_plugins_path(paths, plugin_type)

    if not os.path.exists(plugin_source_path) or os.listdir(plugin_source_path) == []:
        return []

    command = [paths.ansible_doc_path, '--json', '-t', plugin_type, '--list']
    if collection_name:
        command.append(collection_name)
    output = subprocess.check_output(command)
    plugins_list = json.loads(output.decode('utf-8'))

    if not collection_name:
        # Filter out FQCNs
        plugins_list = {
            name: data for name, data in plugins_list.items()
            if '.' not in name or name.startswith('ansible.builtin.')
        }
    else:
        # Filter out without / wrong FQCN
        plugins_list = {
            name: data for name, data in plugins_list.items()
            if name.startswith(collection_name + '.')
        }

    return sorted(plugins_list.keys())


def run_ansible_doc(paths: PathsConfig, plugin_type: str, plugin_names: List[str]) -> dict:
    """
    Runs ansible-doc to retrieve documentation for a given set of plugins in JSON format.

    Plugins must be in FQCN for collections.
    """
    command = [paths.ansible_doc_path, '--json', '-t', plugin_type]
    command.extend(plugin_names)
    output = subprocess.check_output(command)
    return json.loads(output.decode('utf-8'))


def load_plugin_metadata(paths: PathsConfig, plugin_type: str,
                         collection_name: Optional[str],
                         use_ansible_doc: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Collect plugin metadata for all plugins of a given type.

    :arg paths: Paths configuration
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate
    :arg use_ansible_doc: Set to ``True`` to always use ansible-doc to enumerate plugins/modules
    """
    if use_ansible_doc:
        # WARNING: Do not make this the default to this before ansible-base is a requirement!
        plugins_list = list_plugins_ansibledoc(paths, plugin_type, collection_name)
    else:
        plugins_list = list_plugins_walk(paths, plugin_type, collection_name)

    result: Dict[str, Dict[str, Any]] = {}
    if not plugins_list:
        return result

    plugins_data = run_ansible_doc(paths, plugin_type, plugins_list)

    for name, data in plugins_data.items():
        processed_data = jsondoc_to_metadata(paths, collection_name, plugin_type, name, data)
        result[processed_data['name']] = processed_data
    return result


def load_plugins(paths: PathsConfig,
                 collection_details: CollectionDetails,
                 version: str,
                 force_reload: bool = False,
                 use_ansible_doc: bool = False) -> List[PluginDescription]:
    """
    Load plugins from ansible-doc.

    :arg paths: Paths configuration
    :arg collection_details: Collection details
    :arg version: The current version. Used for caching data
    :arg force_reload: Set to ``True`` to ignore potentially cached data
    :arg use_ansible_doc: Set to ``True`` to always use ansible-doc to enumerate plugins/modules
    :return: A list of all plugins
    """
    plugin_cache_path = os.path.join(paths.changelog_dir, '.plugin-cache.yaml')
    plugins_data: Dict[str, Any] = {}

    if not force_reload and os.path.exists(plugin_cache_path):
        plugins_data = load_yaml(plugin_cache_path)
        if version != plugins_data['version']:
            LOGGER.info('version {} does not match plugin cache version {}',
                        version, plugins_data['version'])
            plugins_data = {}

    if not plugins_data:
        LOGGER.info('refreshing plugin cache')

        plugins_data['version'] = version
        plugins_data['plugins'] = {}

        collection_name: Optional[str] = None
        if paths.is_collection:
            collection_name = '{}.{}'.format(
                collection_details.get_namespace(), collection_details.get_name())

        for plugin_type in get_documentable_plugins():
            plugins_data['plugins'][plugin_type] = load_plugin_metadata(
                paths, plugin_type, collection_name, use_ansible_doc=use_ansible_doc)

        # remove empty namespaces from plugins
        for section in plugins_data['plugins'].values():
            for plugin in section.values():
                if plugin['namespace'] is None:
                    del plugin['namespace']

        store_yaml(plugin_cache_path, plugins_data)

    plugins = PluginDescription.from_dict(plugins_data['plugins'])

    return plugins

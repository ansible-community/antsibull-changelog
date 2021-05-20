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
import shutil
import subprocess
import tempfile

from typing import Any, Dict, List, Optional

from .ansible import get_documentable_plugins, get_documentable_objects, PLUGIN_EXCEPTIONS
from .config import CollectionDetails, PathsConfig
from .logger import LOGGER
from .yaml import load_yaml, store_yaml


class PluginDescription:
    # pylint: disable=too-few-public-methods
    """
    Stores a description of one plugin.
    """

    category: str
    type: str
    name: str
    namespace: Optional[str]
    description: str
    version_added: Optional[str]

    def __init__(self, plugin_type: str, name: str, namespace: Optional[str],
                 description: str, version_added: Optional[str],
                 category: str = 'plugin'):
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
    def from_dict(data: Dict[str, Dict[str, Dict[str, Any]]],
                  category: str = 'plugin') -> 'List[PluginDescription]':
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
                    category=category,
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


def extract_namespace(paths: PathsConfig, collection_name: Optional[str], filename: str) -> str:
    """
    Given a filename of a module, will extract the module's namespace.
    """
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
    return'.'.join(namespace_list)


def jsondoc_to_metadata(paths: PathsConfig,  # pylint: disable=too-many-arguments
                        collection_name: Optional[str],
                        plugin_type: str, name: str, data: Dict[str, Any],
                        category: str = 'plugin') -> Dict[str, Any]:
    """
    Convert ``ansible-doc --json`` output to plugin metadata.

    :arg paths: Paths configuration
    :arg collection_name: The name of the collection, if appropriate
    :arg plugin_type: The plugin's or object's type
    :arg name: The plugin's name
    :arg data: The JSON for this plugin returned by ``ansible-doc --json``
    :arg category: Set to ``object`` for roles and playbooks
    """
    namespace: Optional[str] = None
    if collection_name and name.startswith(collection_name + '.'):
        name = name[len(collection_name) + 1:]
    docs: dict = data.get('doc') or dict()
    if category == 'object' and plugin_type == 'role':
        entrypoints: dict = data.get('entry_points') or dict()
        if 'main' in entrypoints:
            docs = entrypoints['main']
    if category == 'plugin' and plugin_type == 'module':
        filename: Optional[str] = docs.get('filename')
        if filename:
            namespace = extract_namespace(paths, collection_name, filename)
        if '.' in name:
            # Flatmapping
            name = name[name.rfind('.') + 1:]
    return {
        'description': docs.get('short_description'),
        'name': name,
        'namespace': namespace,
        'version_added': docs.get('version_added'),
    }


def get_plugins_path(paths: PathsConfig, plugin_type: str, category: str = 'plugin') -> str:
    """
    Return path to plugins of a given type.
    """
    if paths.is_collection:
        if category == 'object':
            return os.path.join(paths.base_dir, '{0}s'.format(plugin_type))
        return os.path.join(
            paths.base_dir, 'plugins', 'modules' if plugin_type == 'module' else plugin_type)
    lib_ansible = os.path.join(paths.base_dir, 'lib', 'ansible')
    if plugin_type == 'module':
        return os.path.join(lib_ansible, 'modules')
    return os.path.join(lib_ansible, 'plugins', plugin_type)


def list_plugins_walk(paths: PathsConfig,
                      playbook_dir: Optional[str],  # pylint: disable=unused-argument
                      plugin_type: str,
                      collection_name: Optional[str]) -> List[str]:
    """
    Find all plugins of a type in a collection, or in Ansible-base. Uses os.walk().

    This will also work with Ansible 2.9.

    :arg paths: Paths configuration
    :arg playbook_dir: Value for the ``--playbook-dir`` argument of ``ansible-doc``
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
            if not paths.is_collection and dirpath == plugin_source_path:
                # Skip files which are *not* plugins/modules, but live in these directories inside
                # ansible-base/-core.
                if (plugin_type, filename) in PLUGIN_EXCEPTIONS:
                    continue
            path = follow_links(os.path.join(dirpath, filename))
            path = os.path.splitext(path)[0]
            relpath = os.path.relpath(path, plugin_source_path)
            if not paths.is_collection and os.sep in relpath:
                # When listing modules in ansible-base/-core, get rid of the namespace.
                relpath = os.path.basename(relpath)
            relname = relpath.replace(os.sep, '.')
            if collection_name:
                relname = '{0}.{1}'.format(collection_name, relname)
            result.add(relname)

    return sorted(result)


def list_plugins_ansibledoc(paths: PathsConfig,
                            playbook_dir: Optional[str],
                            plugin_type: str,
                            collection_name: Optional[str],
                            category: str = 'plugin') -> List[str]:
    """
    Find all plugins of a type in a collection, or in Ansible-base. Uses ansible-doc.

    Note that ansible-doc from Ansible 2.10 or newer is needed for this!

    :arg paths: Paths configuration
    :arg playbook_dir: Value for the ``--playbook-dir`` argument of ``ansible-doc``
    :arg plugin_type: The plugin type to consider
    :arg collection_name: The name of the collection, if appropriate.
    """
    plugin_source_path = get_plugins_path(paths, plugin_type, category)

    if not os.path.exists(plugin_source_path) or os.listdir(plugin_source_path) == []:
        return []

    command = [paths.ansible_doc_path, '--json', '-t', plugin_type, '--list']
    if playbook_dir:
        command.extend(['--playbook-dir', playbook_dir])
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


def run_ansible_doc(paths: PathsConfig, playbook_dir: Optional[str],
                    plugin_type: str, plugin_names: List[str]) -> dict:
    """
    Runs ansible-doc to retrieve documentation for a given set of plugins in JSON format.

    Plugins must be in FQCN for collections.
    """
    command = [paths.ansible_doc_path, '--json', '-t', plugin_type]
    if playbook_dir:
        command.extend(['--playbook-dir', playbook_dir])
    command.extend(plugin_names)
    output = subprocess.check_output(command)
    return json.loads(output.decode('utf-8'))


def load_plugin_metadata(paths: PathsConfig,  # pylint: disable=too-many-arguments
                         playbook_dir: Optional[str],
                         plugin_type: str,
                         collection_name: Optional[str],
                         use_ansible_doc: bool = False,
                         category: str = 'plugin') -> Dict[str, Dict[str, Any]]:
    """
    Collect plugin metadata for all plugins of a given type.

    :arg paths: Paths configuration
    :arg playbook_dir: Value for the ``--playbook-dir`` argument of ``ansible-doc``
    :arg plugin_type: The plugin type or object type to consider
    :arg collection_name: The name of the collection, if appropriate
    :arg use_ansible_doc: Set to ``True`` to always use ansible-doc to enumerate plugins/modules
    :arg category: Set to ``object`` for roles and playbooks
    """
    if use_ansible_doc or category == 'object':
        # WARNING: Do not make this the default to this before ansible-base is a requirement!
        plugins_list = list_plugins_ansibledoc(
            paths, playbook_dir, plugin_type, collection_name, category)
    else:
        plugins_list = list_plugins_walk(paths, playbook_dir, plugin_type, collection_name)

    result: Dict[str, Dict[str, Any]] = {}
    if not plugins_list:
        return result

    plugins_data = run_ansible_doc(paths, playbook_dir, plugin_type, plugins_list)

    for name, data in plugins_data.items():
        processed_data = jsondoc_to_metadata(
            paths, collection_name, plugin_type, name, data, category=category)
        result[processed_data['name']] = processed_data
    return result


class CollectionCopier:
    """
    Creates a copy of a collection to a place where ``--playbook-dir`` can be used
    to prefer this copy of the collection over any installed ones.
    """
    def __init__(self, paths: PathsConfig, namespace: str, name: str):
        self.paths = paths
        self.namespace = namespace
        self.name = name

        self.dir = tempfile.mkdtemp(prefix='antsibull-changelog')

    def __enter__(self):
        try:
            collection_container_dir = os.path.join(
                self.dir, 'collections', 'ansible_collections', self.namespace)
            os.makedirs(collection_container_dir)

            collection_dir = os.path.join(collection_container_dir, self.name)
            shutil.copytree(self.paths.base_dir, collection_dir, symlinks=True)

            new_paths = PathsConfig.force_collection(
                collection_dir, ansible_doc_bin=self.paths.ansible_doc_path)
            return self.dir, new_paths
        except Exception:  # pylint: disable=broad-except
            shutil.rmtree(self.dir, ignore_errors=True)
            raise

    def __exit__(self, type_, value, traceback_):
        shutil.rmtree(self.dir, ignore_errors=True)


def _load_collection_plugins(plugins_data: Dict[str, Any],
                             paths: PathsConfig,
                             collection_details: CollectionDetails,
                             use_ansible_doc: bool) -> None:
    collection_name = '{}.{}'.format(
        collection_details.get_namespace(), collection_details.get_name())

    with CollectionCopier(
            paths, collection_details.get_namespace(), collection_details.get_name()
    ) as (playbook_dir, new_paths):
        for plugin_type in get_documentable_plugins():
            plugins_data['plugins'][plugin_type] = load_plugin_metadata(
                new_paths, playbook_dir, plugin_type, collection_name,
                use_ansible_doc=use_ansible_doc)

        for object_type in get_documentable_objects():
            plugins_data['objects'][object_type] = load_plugin_metadata(
                new_paths, playbook_dir, object_type, collection_name,
                use_ansible_doc=use_ansible_doc, category='object')


def _load_ansible_plugins(plugins_data: Dict[str, Any], paths: PathsConfig,
                          use_ansible_doc: bool) -> None:
    for plugin_type in get_documentable_plugins():
        plugins_data['plugins'][plugin_type] = load_plugin_metadata(
            paths, None, plugin_type, None, use_ansible_doc=use_ansible_doc)


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
        plugins_data['objects'] = {}

        if paths.is_collection:
            _load_collection_plugins(plugins_data, paths, collection_details, use_ansible_doc)
        else:
            _load_ansible_plugins(plugins_data, paths, use_ansible_doc)

        # remove empty namespaces from plugins
        for category in ('plugins', 'objects'):
            for section in plugins_data[category].values():
                for plugin in section.values():
                    if plugin['namespace'] is None:
                        del plugin['namespace']

        store_yaml(plugin_cache_path, plugins_data)

    plugins = PluginDescription.from_dict(plugins_data['plugins'])
    if 'objects' in plugins_data:
        plugins.extend(PluginDescription.from_dict(plugins_data['objects'], category='object'))

    return plugins

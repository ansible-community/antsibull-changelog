# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Configuration classes for paths and changelogs.
"""

import collections
import os

from typing import Mapping, Optional

from .errors import ChangelogError
from .logger import LOGGER
from .yaml import load_yaml, store_yaml


def _is_other_project_config(config_path: str) -> bool:
    try:
        config = load_yaml(config_path)
        return config.get('is_other_project', False)
    except:  # pylint: disable=bare-except;  # noqa: E722
        return False


class PathsConfig:
    """
    Configuration for paths.
    """

    is_collection: bool
    is_other_project: bool

    base_dir: str
    galaxy_path: Optional[str]
    changelog_dir: str
    config_path: str
    ansible_doc_path: str

    @staticmethod
    def _changelog_dir(base_dir: str) -> str:
        return os.path.join(base_dir, 'changelogs')

    @staticmethod
    def _config_path(changelog_dir: str) -> str:
        return os.path.join(changelog_dir, 'config.yaml')

    def __init__(self, is_collection: bool, base_dir: str, galaxy_path: Optional[str],
                 ansible_doc_path: Optional[str], is_other_project: bool = False
                 ):  # pylint: disable=too-many-arguments
        """
        Forces configuration with given base path.

        :arg base_dir: Base directory of Ansible checkout or collection checkout
        :arg galaxy_path: Path to galaxy.yml for collection checkouts
        :arg ansible_doc_path: Path to ``ansible-doc``
        :arg is_other_project: Flag whether this config belongs to another project than
                               ansible-core or an Ansible collection
        """
        self.is_collection = is_collection
        self.is_other_project = is_other_project
        self.base_dir = base_dir
        if not self.is_other_project and galaxy_path and not os.path.exists(galaxy_path):
            LOGGER.debug('Cannot find galaxy.yml')
            galaxy_path = None
        self.galaxy_path = galaxy_path
        self.changelog_dir = PathsConfig._changelog_dir(self.base_dir)
        self.config_path = PathsConfig._config_path(self.changelog_dir)
        self.ansible_doc_path = ansible_doc_path or 'ansible-doc'

    @staticmethod
    def force_collection(base_dir: str,
                         ansible_doc_bin: Optional[str] = None) -> 'PathsConfig':
        """
        Forces configuration for collection checkout with given base path.

        :arg base_dir: Base directory of collection checkout
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(True, base_dir, os.path.join(base_dir, 'galaxy.yml'), ansible_doc_bin)

    @staticmethod
    def force_ansible(base_dir: str,
                      ansible_doc_bin: Optional[str] = None) -> 'PathsConfig':
        """
        Forces configuration with given ansible-core/-base base path.

        :type base_dir: Base directory of ansible-core/-base checkout
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(False, base_dir, None, ansible_doc_bin)

    @staticmethod
    def force_other(base_dir: str,
                    ansible_doc_bin: Optional[str] = None) -> 'PathsConfig':
        """
        Forces configuration for a project that's neither ansible-core/-base nor an
        Ansible collection.

        :type base_dir: Base directory of the project
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(False, base_dir, None, ansible_doc_bin, is_other_project=True)

    @staticmethod
    def detect(is_collection: Optional[bool] = None,
               ansible_doc_bin: Optional[str] = None,
               is_other_project: Optional[bool] = None) -> 'PathsConfig':
        """
        Detect paths configuration from current working directory.

        :raises ChangelogError: cannot identify collection, ansible-core/-base checkout,
                                or other project.
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        previous: Optional[str] = None
        base_dir = os.getcwd()
        while True:
            changelog_dir = PathsConfig._changelog_dir(base_dir)
            config_path = PathsConfig._config_path(changelog_dir)
            if os.path.exists(changelog_dir) and os.path.exists(config_path):
                if is_other_project is True or (
                        not is_collection and _is_other_project_config(config_path)):
                    # This is neither ansible-core/-base nor an Ansible collection,
                    # but explicitly marked as an 'other project'
                    return PathsConfig(False, base_dir, None, ansible_doc_bin,
                                       is_other_project=True)
                galaxy_path = os.path.join(base_dir, 'galaxy.yml')
                if os.path.exists(galaxy_path) or is_collection is True:
                    # We are in a collection and assume ansible-doc is available in $PATH
                    return PathsConfig(True, base_dir, galaxy_path, ansible_doc_bin)
                ansible_lib_dir = os.path.join(base_dir, 'lib', 'ansible')
                if os.path.exists(ansible_lib_dir) or is_collection is False:
                    # We are in a checkout of ansible/ansible
                    return PathsConfig(False, base_dir, None, ansible_doc_bin)
            previous, base_dir = base_dir, os.path.dirname(base_dir)
            if previous == base_dir:
                raise ChangelogError('Cannot identify collection, ansible-core/-base'
                                     ' checkout, or other project.')


def load_galaxy_metadata(paths: PathsConfig) -> dict:
    """
    Load galaxy.yml metadata.

    :arg paths: Paths configuration.
    :return: The contents of ``galaxy.yaml``.
    """
    path = paths.galaxy_path
    if path is None:
        raise ChangelogError('Cannot find galaxy.yml')
    return load_yaml(path)


class CollectionDetails:
    """
    Stores information about a collection. Can auto-populate from galaxy.yml.
    """

    paths: PathsConfig
    galaxy_yaml_loaded: bool

    namespace: Optional[str]
    name: Optional[str]
    version: Optional[str]
    flatmap: Optional[bool]

    def __init__(self, paths: PathsConfig):
        self.paths = paths
        self.galaxy_yaml_loaded = False
        self.namespace = None
        self.name = None
        self.version = None
        self.flatmap = None

    def _parse_galaxy_yaml(self, galaxy_yaml):
        self.galaxy_yaml_loaded = True
        if not isinstance(galaxy_yaml, dict):
            raise ChangelogError('galaxy.yml must be a dictionary')
        if self.namespace is None and isinstance(galaxy_yaml.get('namespace'), str):
            self.namespace = galaxy_yaml.get('namespace')
        if self.name is None and isinstance(galaxy_yaml.get('name'), str):
            self.name = galaxy_yaml.get('name')
        if self.version is None and isinstance(galaxy_yaml.get('version'), str):
            self.version = galaxy_yaml.get('version')
        if self.flatmap is None and galaxy_yaml.get('type') is not None:
            self.flatmap = galaxy_yaml['type'] == 'flatmap'

    def _load_galaxy_yaml(self, needed_var: str,
                          what_for: Optional[str] = None,
                          help_text: Optional[str] = None):
        if self.galaxy_yaml_loaded:
            return
        if not self.paths.is_collection:
            raise Exception('Internal error: cannot get collection details for non-collection')

        if what_for is None:
            what_for = 'load field "{0}"'.format(needed_var)
        try:
            galaxy_yaml = load_galaxy_metadata(self.paths)
        except Exception as exc:  # pylint: disable=broad-except
            msg = 'Cannot find galaxy.yaml to {0}: {1}'.format(what_for, exc)
            if help_text is not None:
                msg = '{0}. {1}'.format(msg, help_text)
            raise ChangelogError(msg) from exc

        self._parse_galaxy_yaml(galaxy_yaml)

    def get_namespace(self) -> str:
        """
        Get collection's namespace.
        """
        help_text = 'You can explicitly specify the value with `--collection-namespace`.'
        if self.namespace is None:
            self._load_galaxy_yaml('namespace', help_text=help_text)
        namespace = self.namespace
        if namespace is None:
            raise ChangelogError('Cannot find "namespace" field in galaxy.yaml. ' + help_text)
        return namespace

    def get_name(self) -> str:
        """
        Get collection's name.
        """
        help_text = 'You can explicitly specify the value with `--collection-name`.'
        if self.name is None:
            self._load_galaxy_yaml('name', help_text=help_text)
        name = self.name
        if name is None:
            raise ChangelogError('Cannot find "name" field in galaxy.yaml. ' + help_text)
        return name

    def get_version(self) -> str:
        """
        Get collection's version.
        """
        help_text = 'You can explicitly specify the value with `--version`.'
        if self.version is None:
            self._load_galaxy_yaml('version', help_text=help_text)
        version = self.version
        if version is None:
            raise ChangelogError('Cannot find "version" field in galaxy.yaml. ' + help_text)
        return version

    def get_flatmap(self) -> Optional[bool]:
        """
        Get collection's flatmap flag.
        """
        help_text = 'You can explicitly specify the value with `--collection-flatmap`.'
        if self.flatmap is None and not self.galaxy_yaml_loaded:
            self._load_galaxy_yaml('type', what_for='determine flatmapping', help_text=help_text)
        return self.flatmap


DEFAULT_SECTIONS = [
    ['major_changes', 'Major Changes'],
    ['minor_changes', 'Minor Changes'],
    ['breaking_changes', 'Breaking Changes / Porting Guide'],
    ['deprecated_features', 'Deprecated Features'],
    ['removed_features', 'Removed Features (previously deprecated)'],
    ['security_fixes', 'Security Fixes'],
    ['bugfixes', 'Bugfixes'],
    ['known_issues', 'Known Issues'],
]


class ChangelogConfig:
    # pylint: disable=too-many-instance-attributes
    """
    Configuration for changelogs.
    """

    paths: PathsConfig
    collection_details: CollectionDetails

    config: dict
    is_collection: bool
    title: Optional[str]
    notes_dir: str
    prelude_name: str
    prelude_title: str
    new_plugins_after_name: str
    changes_file: str
    changes_format: str
    keep_fragments: bool
    prevent_known_fragments: bool
    use_fqcn: bool
    archive_path_template: Optional[str]
    changelog_filename_template: str
    changelog_filename_version_depth: int
    mention_ancestor: bool
    trivial_section_name: str
    release_tag_re: str
    pre_release_tag_re: str
    always_refresh: str
    ignore_other_fragment_extensions: bool
    sanitize_changelog: bool
    flatmap: Optional[bool]
    use_semantic_versioning: bool
    is_other_project: bool
    sections: Mapping[str, str]

    def __init__(self, paths: PathsConfig, collection_details: CollectionDetails, config: dict,
                 ignore_is_other_project: bool = False):
        """
        Create changelog config from dictionary.
        """
        self.paths = paths
        self.collection_details = collection_details
        self.config = config

        self.is_collection = paths.is_collection
        self.title = self.config.get('title')
        self.notes_dir = self.config.get('notesdir', 'fragments')
        self.prelude_name = self.config.get('prelude_section_name', 'release_summary')
        self.prelude_title = self.config.get('prelude_section_title', 'Release Summary')
        self.new_plugins_after_name = self.config.get('new_plugins_after_name', '')  # not used
        self.changes_file = self.config.get('changes_file', '.changes.yaml')
        self.changes_format = self.config.get('changes_format', 'classic')
        self.keep_fragments = self.config.get('keep_fragments', self.changes_format == 'classic')
        self.prevent_known_fragments = self.config.get(
            'prevent_known_fragments', self.keep_fragments)
        self.use_fqcn = self.config.get('use_fqcn', False)
        self.archive_path_template = self.config.get('archive_path_template')
        self.changelog_filename_template = self.config.get(
            'changelog_filename_template', 'CHANGELOG-v%s.rst')
        self.changelog_filename_version_depth = self.config.get(
            'changelog_filename_version_depth', 2)
        self.mention_ancestor = self.config.get('mention_ancestor', True)
        self.trivial_section_name = self.config.get('trivial_section_name', 'trivial')
        self.sanitize_changelog = self.config.get('sanitize_changelog', False)
        always_refresh = self.config.get('always_refresh', self.changes_format == 'classic')
        if always_refresh is True:
            always_refresh = 'full'
        if always_refresh is False:
            always_refresh = 'none'
        self.always_refresh = always_refresh
        self.ignore_other_fragment_extensions = self.config.get(
            'ignore_other_fragment_extensions', False)
        self.flatmap = self.config.get('flatmap')
        self.use_semantic_versioning = True
        self.is_other_project = self.config.get('is_other_project', False)

        # The following are only relevant for ansible-core/-base and other projects:
        self.release_tag_re = self.config.get(
            'release_tag_re', r'((?:[\d.ab]|rc)+)')
        self.pre_release_tag_re = self.config.get(
            'pre_release_tag_re', r'(?P<pre_release>\.\d+(?:[ab]|rc)+\d*)$')
        if not self.is_collection:
            self.use_semantic_versioning = self.config.get('use_semantic_versioning', False)

        sections = collections.OrderedDict([(self.prelude_name, self.prelude_title)])
        for section_name, section_title in self.config.get('sections', DEFAULT_SECTIONS):
            sections[section_name] = section_title
        self.sections = sections

        self._validate_config(ignore_is_other_project)

    def _validate_config(self, ignore_is_other_project: bool) -> None:
        """
        Basic config validation.
        """
        if self.is_other_project != self.paths.is_other_project and not ignore_is_other_project:
            raise ChangelogError(
                'is_other_project must be {0}'.format(self.is_other_project))
        if self.is_other_project and self.is_collection and not ignore_is_other_project:
            raise ChangelogError('is_other_project must not be True for collections')
        if self.changes_format not in ('classic', 'combined'):
            raise ChangelogError('changes_format must be one of "classic" and "combined"')
        if self.changes_format == 'classic' and not self.keep_fragments:
            raise ChangelogError('changes_format == "classic" cannot be '
                                 'combined with keep_fragments == False')
        if self.changes_format == 'classic' and not self.prevent_known_fragments:
            raise ChangelogError('changes_format == "classic" cannot be '
                                 'combined with prevent_known_fragments == False')

    def store(self) -> None:  # noqa: C901
        """
        Store changelog configuration file to disk.
        """
        config: dict = {
            'notesdir': self.notes_dir,
            'changes_file': self.changes_file,
            'changes_format': self.changes_format,
            'mention_ancestor': self.mention_ancestor,
            'keep_fragments': self.keep_fragments,
            'use_fqcn': self.use_fqcn,
            'changelog_filename_template': self.changelog_filename_template,
            'changelog_filename_version_depth': self.changelog_filename_version_depth,
            'prelude_section_name': self.prelude_name,
            'prelude_section_title': self.prelude_title,
            'new_plugins_after_name': self.new_plugins_after_name,
            'trivial_section_name': self.trivial_section_name,
            'ignore_other_fragment_extensions': self.ignore_other_fragment_extensions,
            'sanitize_changelog': self.sanitize_changelog
        }
        if not self.is_collection:
            if self.use_semantic_versioning:
                config['use_semantic_versioning'] = True
            else:
                config.update({
                    'release_tag_re': self.release_tag_re,
                    'pre_release_tag_re': self.pre_release_tag_re,
                })
        if self.title is not None:
            config['title'] = self.title
        should_always_refresh = (self.changes_format == 'classic')
        if self.always_refresh != ('full' if should_always_refresh else 'none'):
            config['always_refresh'] = self.always_refresh
        if self.keep_fragments != self.prevent_known_fragments:
            config['prevent_known_fragments'] = self.prevent_known_fragments
        if self.flatmap is not None:
            config['flatmap'] = self.flatmap
        if self.archive_path_template is not None:
            config['archive_path_template'] = self.archive_path_template
        if self.is_other_project:
            config['is_other_project'] = self.is_other_project

        sections = []
        for key, value in self.sections.items():
            if key == self.prelude_name and value == self.prelude_title:
                continue
            sections.append([key, value])
        config['sections'] = sections

        store_yaml(self.paths.config_path, config)

    @staticmethod
    def load(paths: PathsConfig, collection_details: CollectionDetails,
             ignore_is_other_project: bool = False) -> 'ChangelogConfig':
        """
        Load changelog configuration file from disk.
        """
        config = load_yaml(paths.config_path)
        if not isinstance(config, dict):
            raise ChangelogError('{0} must be a dictionary'.format(paths.config_path))
        return ChangelogConfig(paths, collection_details, config,
                               ignore_is_other_project=ignore_is_other_project)

    @staticmethod
    def default(paths: PathsConfig, collection_details: CollectionDetails,
                title: Optional[str] = None) -> 'ChangelogConfig':
        """
        Create default changelog config.

        :type title: Title of the project
        """
        config = {
            'changes_file': 'changelog.yaml',
            'changes_format': 'combined',
            'changelog_filename_template': '../CHANGELOG.rst',
            'changelog_filename_version_depth': 0,
            'new_plugins_after_name': 'removed_features',
            'sections': DEFAULT_SECTIONS,
            'use_fqcn': True,
            'ignore_other_fragment_extensions': True,
            'sanitize_changelog': True,
        }
        if title is not None:
            config['title'] = title
        if paths.is_other_project:
            config['is_other_project'] = True
            config['use_semantic_versioning'] = True
        return ChangelogConfig(paths, collection_details, config)

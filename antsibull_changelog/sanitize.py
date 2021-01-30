# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Sanitizing changelog.yaml files
"""

import collections.abc
import re

from typing import Any, Dict, List, Mapping, Optional, Union

import packaging.version
import semantic_version

from .ansible import get_documentable_plugins, OBJECT_TYPES, OTHER_PLUGIN_TYPES
from .config import ChangelogConfig


ISO_DATE_REGEX = re.compile('^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$')


class Sanitizer:  # pylint: disable=too-few-public-methods
    """
    Implements changelog.yaml sanitizier.
    """

    config: ChangelogConfig

    def __init__(self, config: ChangelogConfig):
        self.config = config
        self.plugin_types = set(get_documentable_plugins())
        self.plugin_types.update(OTHER_PLUGIN_TYPES)

    def _is_version(self, version: Any, allow_none: bool = False) -> bool:
        try:
            if version is None and allow_none:
                return True
            if not isinstance(version, str):
                return False
            if self.config.use_semantic_versioning:
                semantic_version.Version(version)
            else:
                packaging.version.Version(version)
            return True
        except ValueError:
            return False

    def _sanitize_ancestor(self, ancestor: Any) -> Optional[str]:
        return ancestor if self._is_version(ancestor, allow_none=True) else None

    @staticmethod
    def _sanitize_date(date: Any) -> Optional[str]:
        if not isinstance(date, str):
            return None
        return date if ISO_DATE_REGEX.match(date) else None

    def _sanitize_changes(self, data: Mapping) -> Dict[str, Union[str, List[str]]]:
        result: Dict[str, Union[str, List[str]]] = {}
        for key, value in data.items():
            if not isinstance(key, str):
                continue
            if key == self.config.prelude_name:
                if isinstance(value, str):
                    result[key] = value
            elif key == self.config.trivial_section_name or key in self.config.sections:
                if isinstance(value, list):
                    entries = []
                    for entry in value:
                        if isinstance(entry, str):
                            entries.append(entry)
                    result[key] = entries
        return result

    def _sanitize_modules(self, data: List,
                          are_modules: bool = True) -> List:
        result: List = []
        if self.config.changes_format == 'classic':
            for entry in data:
                if isinstance(entry, str):
                    result.append(entry)
        else:
            for entry in data:
                if not isinstance(entry, collections.abc.Mapping):
                    continue
                name = entry.get('name')
                if not isinstance(name, str):
                    continue
                description = entry.get('description')
                if not isinstance(description, str):
                    continue
                if are_modules:
                    namespace = entry.get('namespace')
                    if not isinstance(namespace, str):
                        continue
                else:
                    namespace = None
                result.append({
                    'name': name,
                    'description': description,
                    'namespace': namespace,
                })
        return result

    def _sanitize_plugins(self, data: Mapping) -> Dict[str, List]:
        result = {}
        for key, value in data.items():
            if key not in self.plugin_types or not isinstance(value, list):
                continue
            sanitized_value = self._sanitize_modules(value, are_modules=False)
            if sanitized_value:
                result[key] = sanitized_value
        return result

    def _sanitize_objects(self, data: Mapping) -> Dict[str, List]:
        result = {}
        for key, value in data.items():
            if key not in OBJECT_TYPES or not isinstance(value, list):
                continue
            sanitized_value = self._sanitize_modules(value, are_modules=False)
            if sanitized_value:
                result[key] = sanitized_value
        return result

    @staticmethod
    def _sanitize_fragments(data: List) -> List[str]:
        result = []
        for entry in data:
            if isinstance(entry, str):
                result.append(entry)
        return result

    def _sanitize_modules_plugins(self, release: Mapping, result: Dict[str, Any]) -> None:
        modules = release.get('modules')
        if isinstance(modules, list):
            sanitized_modules = self._sanitize_modules(modules)
            if sanitized_modules:
                result['modules'] = sanitized_modules

        plugins = release.get('plugins')
        if isinstance(plugins, collections.abc.Mapping):
            sanitized_plugins = self._sanitize_plugins(plugins)
            if sanitized_plugins:
                result['plugins'] = sanitized_plugins

        objects = release.get('objects')
        if isinstance(objects, collections.abc.Mapping):
            sanitized_objects = self._sanitize_objects(objects)
            if sanitized_objects:
                result['objects'] = sanitized_objects

    def _sanitize_release(self, release: Mapping) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        release_date = self._sanitize_date(release.get('release_date'))
        if release_date is not None:
            result['release_date'] = release_date

        codename = release.get('codename')
        if isinstance(codename, str):
            result['codename'] = codename

        changes = release.get('changes')
        if isinstance(changes, collections.abc.Mapping):
            sanitized_changes = self._sanitize_changes(changes)
            if sanitized_changes:
                result['changes'] = sanitized_changes

        self._sanitize_modules_plugins(release, result)

        fragments = release.get('fragments')
        if isinstance(fragments, list):
            sanitized_fragments = self._sanitize_fragments(fragments)
            if sanitized_fragments:
                result['fragments'] = sanitized_fragments

        return result

    def _sanitize_releases(self, releases: Any) -> Mapping[str, Mapping]:
        if not isinstance(releases, collections.abc.Mapping):
            return {}
        result = {}
        for key, value in releases.items():
            if not self._is_version(key) or not isinstance(value, collections.abc.Mapping):
                continue
            result[key] = self._sanitize_release(value)
        return result

    def sanitize(self, data: Any) -> Dict[str, Any]:
        """
        Given an arbitrary object, sanitizes it so it a valid changelog.yaml object.
        """
        if not isinstance(data, collections.abc.Mapping):
            # FUBAR: return an empty changelog
            return {
                'ancestor': None,
                'releases': {}
            }
        result = {
            'ancestor': self._sanitize_ancestor(data.get('ancestor')),
            'releases': self._sanitize_releases(data.get('releases')),
        }
        return result


def sanitize_changes(data: Any, config: ChangelogConfig) -> Dict[str, Any]:
    """
    Given an arbitrary object, sanitizes it so it a valid changelog.yaml object.
    """
    return Sanitizer(config).sanitize(data)

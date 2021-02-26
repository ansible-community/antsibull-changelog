# -*- coding: utf-8 -*-
# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Changelog fragment loading, modification and linting.
"""

import os

from typing import Any, Dict, List, Optional, Tuple, Union

import docutils.utils
import rstcheck

from .ansible import get_documentable_plugins, OBJECT_TYPES, OTHER_PLUGIN_TYPES
from .config import ChangelogConfig, PathsConfig
from .errors import ChangelogError
from .logger import LOGGER
from .yaml import load_yaml


class ChangelogFragment:
    """
    A changelog fragment.
    """

    content: Dict[str, Union[List[str], str]]
    path: str
    name: str

    def __init__(self, content: Dict[str, Union[List[str], str]], path: str):
        """
        Create changelog fragment.
        """
        self.content = content
        self.path = path
        self.name = os.path.basename(path)

    def remove(self) -> None:
        """
        Remove changelog fragment from disk.
        """
        try:
            os.remove(self.path)
        except Exception:  # pylint: disable=broad-except
            LOGGER.warning('Cannot remove fragment {path}'.format(
                path=self.path,
            ))

    def move_to(self, directory: str) -> None:
        """
        Move changelog fragment to a different directory.
        """
        destination = os.path.join(directory, os.path.basename(self.path))
        try:
            os.rename(self.path, destination)
        except Exception:  # pylint: disable=broad-except
            LOGGER.warning('Cannot move fragment {path} to {destination}'.format(
                path=self.path,
                destination=destination,
            ))

    @staticmethod
    def load(path: str) -> 'ChangelogFragment':
        """
        Load a ``ChangelogFragment`` from a file.
        """
        content = load_yaml(path)
        return ChangelogFragment(content, path)

    @staticmethod
    def from_dict(data: Dict[str, Union[List[str], str]], path: str = '') -> 'ChangelogFragment':
        """
        Create a ``ChangelogFragment`` from a dictionary.
        """
        return ChangelogFragment(data, path)

    @staticmethod
    def combine(fragments: List['ChangelogFragment'],
                ignore_obj_adds: bool = False) -> Dict[str, Union[List[str], str]]:
        """
        Combine fragments into a new fragment.
        """
        result: Dict[str, Union[List[str], str]] = {}

        for fragment in fragments:
            for section, content in fragment.content.items():
                if section.startswith('add ') and '.' in section and ignore_obj_adds:
                    continue
                if isinstance(content, list):
                    lines = result.get(section)
                    if lines is None:
                        lines = []
                        result[section] = lines
                    elif not isinstance(lines, list):
                        raise ChangelogError(
                            'Cannot append list to string for section "{0}"'.format(section))

                    lines.extend(content)
                else:
                    result[section] = content

        return result


class ChangelogFragmentLinter:
    # pylint: disable=too-few-public-methods
    """
    Linter for ``ChangelogFragment`` objects.
    """

    def __init__(self, config: ChangelogConfig):
        """
        Create changelog fragment linter.
        """
        self.config = config

    def _lint_add_section(self, errors: List[Tuple[str, int, int, str]],
                          fragment: ChangelogFragment, section: str,
                          obj_class: str, obj_type: str, entries: List
                          # pylint: disable=too-many-arguments
                          ) -> None:
        """
        Lint special 'add (object|plugin).(type)' sections.
        """
        is_modules = False
        if obj_class == 'object':
            if obj_type not in OBJECT_TYPES:
                errors.append((fragment.path, 0, 0,
                               'section "%s"\'s type must be one of %s, not "%s"' % (
                                   section, ', '.join(OBJECT_TYPES), obj_type)))
        elif obj_class == 'plugin':
            if obj_type not in get_documentable_plugins() and obj_type not in OTHER_PLUGIN_TYPES:
                errors.append((fragment.path, 0, 0,
                               'section "%s"\'s type must be one of %s, %s, not "%s"' % (
                                   section,
                                   ', '.join(get_documentable_plugins()),
                                   ', '.join(OTHER_PLUGIN_TYPES),
                                   obj_type)))

            is_modules = obj_type == 'module'
        else:
            errors.append((fragment.path, 0, 0,
                           'section "%s"\'s name must be of format '
                           '"add (object|plugin).(type)"' % (section, )))

        if not isinstance(entries, list):
            errors.append((fragment.path, 0, 0,
                           'section "%s" must be type list '
                           'not %s' % (section, type(entries).__name__)))
        else:
            self._lint_entries(errors, fragment, section, is_modules, entries)

    @staticmethod
    def _lint_entries(errors: List[Tuple[str, int, int, str]],
                      fragment: ChangelogFragment, section: str, is_modules: bool,
                      entries: Any) -> None:
        """
        Lint entries in a special 'add (object|plugin).(type)' section.
        """
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append((fragment.path, 0, 0,
                               'section "%s" list items must be type dict '
                               'not %s' % (section, type(entry).__name__)))
                continue

            if not isinstance(entry.get('name'), str):
                errors.append((fragment.path, 0, 0,
                               'section "%s" entry #%s must have a "name" entry '
                               'of type string' % (section, index)))
            if not isinstance(entry.get('description'), str):
                errors.append((fragment.path, 0, 0,
                               'section "%s" entry #%s must have a "description" entry '
                               'of type string' % (section, index)))
            if not is_modules and entry.get('namespace') is not None:
                errors.append((fragment.path, 0, 0,
                               'section "%s" entry #%s must have a "namespace" entry '
                               'of type string' % (section, index)))
            if is_modules and not isinstance(entry.get('namespace'), str):
                errors.append((fragment.path, 0, 0,
                               'section "%s" entry #%s must not have a non-null "namespace" '
                               'entry' % (section, index)))

            invalid_keys = sorted([
                k for k in entry if k not in ('name', 'description', 'namespace')])
            if invalid_keys:
                errors.append((fragment.path, 0, 0,
                               'section "%s" entry #%s has invalid keys %s' % (
                                   section, index,
                                   ', '.join(['"%s"' % k for k in invalid_keys]))))

    def _lint_section(self, errors: List[Tuple[str, int, int, str]],
                      fragment: ChangelogFragment, section: str,
                      lines: Any) -> None:
        """
        Lint a section of a changelog fragment.
        """
        if section.startswith('add ') and '.' in section:
            obj_class, obj_type = section[4:].split('.', 1)
            self._lint_add_section(errors, fragment, section, obj_class, obj_type, lines)
            return
        if section == self.config.prelude_name:
            if not isinstance(lines, str):
                errors.append((fragment.path, 0, 0,
                               'section "%s" must be type str '
                               'not %s' % (section, type(lines).__name__)))
        else:
            # doesn't account for prelude but only the RM should be adding those
            if not isinstance(lines, list):
                errors.append((fragment.path, 0, 0,
                               'section "%s" must be type list '
                               'not %s' % (section, type(lines).__name__)))

            if section not in self.config.sections and section != self.config.trivial_section_name:
                errors.append((fragment.path, 0, 0, 'invalid section: %s' % section))

    @staticmethod
    def _lint_lines(errors: List[Tuple[str, int, int, str]],
                    fragment: ChangelogFragment, section: str,
                    lines: Any) -> None:
        """
        Lint lines of a changelog fragment.
        """
        if isinstance(lines, list) and not (section.startswith('add ') and '.' in section):
            for line in lines:
                if not isinstance(line, str):
                    errors.append((fragment.path, 0, 0,
                                   'section "%s" list items must be type str '
                                   'not %s' % (section, type(line).__name__)))
                    continue

                results = rstcheck.check(
                    line, filename=fragment.path,
                    report_level=docutils.utils.Reporter.WARNING_LEVEL)
                errors += [(fragment.path, 0, 0, result[1]) for result in results]
        elif isinstance(lines, str):
            results = rstcheck.check(
                lines, filename=fragment.path,
                report_level=docutils.utils.Reporter.WARNING_LEVEL)
            errors += [(fragment.path, 0, 0, result[1]) for result in results]

    def lint(self, fragment: ChangelogFragment) -> List[Tuple[str, int, int, str]]:
        """
        Lint a ``ChangelogFragment``.

        :arg fragment: The changelog fragment to lint
        :return: A list of errors. If empty, the changelog fragment is valid.
        """
        errors: List[Tuple[str, int, int, str]] = []

        if isinstance(fragment.content, dict):  # type: ignore
            for section, lines in fragment.content.items():
                self._lint_section(errors, fragment, section, lines)
                self._lint_lines(errors, fragment, section, lines)

        else:
            errors.append((fragment.path, 0, 0,
                           'file must be a mapping not %s' % (type(fragment.content).__name__, )))

        return errors


def load_fragments(paths: PathsConfig, config: ChangelogConfig,
                   fragment_paths: Optional[List[str]] = None,
                   exceptions: Optional[List[Tuple[str, Exception]]] = None,
                   fragments_dir: Optional[str] = None,
                   ) -> List[ChangelogFragment]:
    """
    Load changelog fragments from disk.

    :arg path: Paths configuration
    :arg config: Changelog configuration
    :arg fragment_paths: List of changelog fragment paths. If not given, all will be used
    :arg fragments_dir: Path where to load changelog fragments from. If not given, the default
                        path will be used.
    :arg exceptions: If given, exceptions during loading will be stored in this list instead
                     of being propagated
    """
    if not fragment_paths:
        if fragments_dir is None:
            fragments_dir = os.path.join(paths.changelog_dir, config.notes_dir)
        if os.path.isdir(fragments_dir):
            fragment_paths = [
                os.path.join(fragments_dir, path)
                for path in os.listdir(fragments_dir)
                if not path.startswith('.')]
            if config.ignore_other_fragment_extensions:
                fragment_paths = [
                    path for path in fragment_paths if any(
                        path.endswith(ext) for ext in ('.yml', '.yaml'))]
        else:
            fragment_paths = []

    fragments: List[ChangelogFragment] = []

    for path in fragment_paths:
        try:
            fragments.append(ChangelogFragment.load(path))
        except Exception as ex:  # pylint: disable=broad-except
            if exceptions is not None:
                exceptions.append((path, ex))
            else:
                raise ChangelogError(str(ex)) from ex

    return fragments

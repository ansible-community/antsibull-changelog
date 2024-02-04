# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Changelog fragment loading, modification and linting.
"""

from __future__ import annotations

import os
from typing import Any

from .ansible import OBJECT_TYPES, OTHER_PLUGIN_TYPES, get_documentable_plugins
from .config import ChangelogConfig, PathsConfig, TextFormat
from .errors import ChangelogError
from .logger import LOGGER
from .rstcheck import check_rst_content
from .yaml import load_yaml


class ChangelogFragment:
    """
    A changelog fragment.
    """

    content: dict[str, list[str] | str]
    path: str
    name: str
    fragment_format: TextFormat

    def __init__(
        self,
        content: dict[str, list[str] | str],
        path: str,
        fragment_format: TextFormat = TextFormat.RESTRUCTURED_TEXT,
    ):
        """
        Create changelog fragment.
        """
        self.content = content
        self.path = path
        self.name = os.path.basename(path)
        self.fragment_format = fragment_format

    def remove(self) -> None:
        """
        Remove changelog fragment from disk.
        """
        try:
            os.remove(self.path)
        except Exception:  # pylint: disable=broad-except
            LOGGER.warning(
                "Cannot remove fragment {path}".format(
                    path=self.path,
                )
            )

    def move_to(self, directory: str) -> None:
        """
        Move changelog fragment to a different directory.
        """
        destination = os.path.join(directory, os.path.basename(self.path))
        try:
            os.rename(self.path, destination)
        except Exception:  # pylint: disable=broad-except
            LOGGER.warning(
                "Cannot move fragment {path} to {destination}".format(
                    path=self.path,
                    destination=destination,
                )
            )

    @staticmethod
    def load(
        path: str, fragment_format: TextFormat = TextFormat.RESTRUCTURED_TEXT
    ) -> "ChangelogFragment":
        """
        Load a ``ChangelogFragment`` from a file.
        """
        content = load_yaml(path)
        return ChangelogFragment(content, path, fragment_format=fragment_format)

    @staticmethod
    def from_dict(
        data: dict[str, list[str] | str],
        path: str = "",
        fragment_format: TextFormat = TextFormat.RESTRUCTURED_TEXT,
    ) -> "ChangelogFragment":
        """
        Create a ``ChangelogFragment`` from a dictionary.
        """
        return ChangelogFragment(data, path, fragment_format=fragment_format)

    @staticmethod
    def combine(
        fragments: list["ChangelogFragment"], ignore_obj_adds: bool = False
    ) -> dict[str, list[str] | str]:
        """
        Combine fragments into a new fragment.
        """
        result: dict[str, list[str] | str] = {}

        for fragment in fragments:
            for section, content in fragment.content.items():
                if section.startswith("add ") and "." in section and ignore_obj_adds:
                    continue
                if isinstance(content, list):
                    lines = result.get(section)
                    if lines is None:
                        lines = []
                        result[section] = lines
                    elif not isinstance(lines, list):
                        raise ChangelogError(
                            'Cannot append list to string for section "{0}"'.format(
                                section
                            )
                        )

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

    def _lint_add_section(
        self,
        errors: list[tuple[str, int, int, str]],
        fragment: ChangelogFragment,
        section: str,
        obj_class: str,
        obj_type: str,
        entries: list,
        # pylint: disable=too-many-arguments
    ) -> None:
        """
        Lint special 'add (object|plugin).(type)' sections.
        """
        is_modules = False
        if obj_class == "object":
            if obj_type not in OBJECT_TYPES:
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s"\'s type must be one of %s, not "%s"'
                        % (section, ", ".join(OBJECT_TYPES), obj_type),
                    )
                )
        elif obj_class == "plugin":
            if (
                obj_type not in get_documentable_plugins()
                and obj_type not in OTHER_PLUGIN_TYPES
            ):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s"\'s type must be one of %s, %s, not "%s"'
                        % (
                            section,
                            ", ".join(get_documentable_plugins()),
                            ", ".join(OTHER_PLUGIN_TYPES),
                            obj_type,
                        ),
                    )
                )

            is_modules = obj_type == "module"
        else:
            errors.append(
                (
                    fragment.path,
                    0,
                    0,
                    'section "%s"\'s name must be of format '
                    '"add (object|plugin).(type)"' % (section,),
                )
            )

        if not isinstance(entries, list):
            errors.append(
                (
                    fragment.path,
                    0,
                    0,
                    'section "%s" must be type list '
                    "not %s" % (section, type(entries).__name__),
                )
            )
        else:
            self._lint_entries(errors, fragment, section, is_modules, entries)

    @staticmethod
    def _lint_entries(
        errors: list[tuple[str, int, int, str]],
        fragment: ChangelogFragment,
        section: str,
        is_modules: bool,
        entries: Any,
    ) -> None:
        """
        Lint entries in a special 'add (object|plugin).(type)' section.
        """
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" list items must be type dict '
                        "not %s" % (section, type(entry).__name__),
                    )
                )
                continue

            if not isinstance(entry.get("name"), str):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" entry #%s must have a "name" entry '
                        "of type string" % (section, index),
                    )
                )
            if not isinstance(entry.get("description"), str):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" entry #%s must have a "description" entry '
                        "of type string" % (section, index),
                    )
                )
            if not is_modules and entry.get("namespace") is not None:
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" entry #%s must have a "namespace" entry '
                        "of type string" % (section, index),
                    )
                )
            if is_modules and not isinstance(entry.get("namespace"), str):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" entry #%s must not have a non-null "namespace" '
                        "entry" % (section, index),
                    )
                )

            invalid_keys = sorted(
                [k for k in entry if k not in ("name", "description", "namespace")]
            )
            if invalid_keys:
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" entry #%s has invalid keys %s'
                        % (
                            section,
                            index,
                            ", ".join(['"%s"' % k for k in invalid_keys]),
                        ),
                    )
                )

    def _lint_section(
        self,
        errors: list[tuple[str, int, int, str]],
        fragment: ChangelogFragment,
        section: str,
        lines: Any,
    ) -> None:
        """
        Lint a section of a changelog fragment.
        """
        if section.startswith("add ") and "." in section:
            obj_class, obj_type = section[4:].split(".", 1)
            self._lint_add_section(
                errors, fragment, section, obj_class, obj_type, lines
            )
            return
        if section == self.config.prelude_name:
            if not isinstance(lines, str):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" must be type str '
                        "not %s" % (section, type(lines).__name__),
                    )
                )
        else:
            # doesn't account for prelude but only the RM should be adding those
            if not isinstance(lines, list):
                errors.append(
                    (
                        fragment.path,
                        0,
                        0,
                        'section "%s" must be type list '
                        "not %s" % (section, type(lines).__name__),
                    )
                )

            if section not in self.config.sections and (
                section != self.config.trivial_section_name or section is None
            ):
                errors.append((fragment.path, 0, 0, "invalid section: %s" % section))

    @staticmethod
    def _check_content(text: str, text_format: TextFormat, filename: str) -> list[str]:
        if text_format == TextFormat.RESTRUCTURED_TEXT:
            results = check_rst_content(text, filename=filename)
            return [result[2] for result in results]
        raise ValueError("No validation possible for MarkDown fragments")

    @staticmethod
    def _lint_lines(
        errors: list[tuple[str, int, int, str]],
        fragment: ChangelogFragment,
        section: str,
        lines: Any,
    ) -> None:
        """
        Lint lines of a changelog fragment.
        """
        if isinstance(lines, list) and not (
            section.startswith("add ") and "." in section
        ):
            for line in lines:
                if not isinstance(line, str):
                    errors.append(
                        (
                            fragment.path,
                            0,
                            0,
                            'section "%s" list items must be type str '
                            "not %s" % (section, type(line).__name__),
                        )
                    )
                    continue

                results = ChangelogFragmentLinter._check_content(
                    line, fragment.fragment_format, fragment.path
                )
                errors += [(fragment.path, 0, 0, result[2]) for result in results]
        elif isinstance(lines, str):
            results = ChangelogFragmentLinter._check_content(
                lines, fragment.fragment_format, fragment.path
            )
            errors += [(fragment.path, 0, 0, result[2]) for result in results]

    def lint(self, fragment: ChangelogFragment) -> list[tuple[str, int, int, str]]:
        """
        Lint a ``ChangelogFragment``.

        :arg fragment: The changelog fragment to lint
        :return: A list of errors. If empty, the changelog fragment is valid.
        """
        errors: list[tuple[str, int, int, str]] = []

        if isinstance(fragment.content, dict):  # type: ignore
            for section, lines in fragment.content.items():
                self._lint_section(errors, fragment, section, lines)
                self._lint_lines(errors, fragment, section, lines)

        else:
            errors.append(
                (
                    fragment.path,
                    0,
                    0,
                    "file must be a mapping not %s"
                    % (type(fragment.content).__name__,),
                )
            )

        return errors


def load_fragments(
    paths: PathsConfig,
    config: ChangelogConfig,
    fragment_paths: list[str] | None = None,
    exceptions: list[tuple[str, Exception]] | None = None,
    fragments_dir: str | None = None,
) -> list[ChangelogFragment]:
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
                if not path.startswith(".")
            ]
            if config.ignore_other_fragment_extensions:
                fragment_paths = [
                    path
                    for path in fragment_paths
                    if any(path.endswith(ext) for ext in (".yml", ".yaml"))
                ]
        else:
            fragment_paths = []

    fragments: list[ChangelogFragment] = []

    for path in fragment_paths:
        try:
            fragments.append(ChangelogFragment.load(path))
        except Exception as ex:  # pylint: disable=broad-except
            if exceptions is not None:
                exceptions.append((path, ex))
            else:
                raise ChangelogError(str(ex)) from ex

    return fragments

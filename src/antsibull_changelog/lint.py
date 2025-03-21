# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Linting for changelog.yaml.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, cast

import packaging.version
import semantic_version
from antsibull_fileutils.yaml import load_yaml_file

from .ansible import OBJECT_TYPES, OTHER_PLUGIN_TYPES, get_documentable_plugins
from .config import ChangelogConfig, CollectionDetails, PathsConfig
from .fragment import ChangelogFragment, ChangelogFragmentLinter

ISO_DATE_REGEX = re.compile("^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$")


class ChangelogYamlLinter:
    """
    Lint a changelogs/changelog.yaml file.
    """

    errors: list[tuple[str, int, int, str]]
    path: str
    strict: bool

    def __init__(
        self,
        path: str,
        *,
        no_semantic_versioning: bool = False,
        preprocess_data: Callable[[dict], None] | None = None,
        strict: bool = False,
    ):
        self.errors = []
        self.path = path
        self.valid_plugin_types = set(get_documentable_plugins())
        self.valid_plugin_types.update(OTHER_PLUGIN_TYPES)
        self.no_semantic_versioning = no_semantic_versioning
        self.preprocess_data = preprocess_data
        self.strict = strict

    def check_version(self, version: Any, message: str) -> Any | None:
        """
        Check that the given version is a valid semantic version.

        :arg version: Version string to check
        :arg message: Message to prepend to error
        :return: A ``semantic_version.Version`` object
        """
        try:
            if not isinstance(version, str):
                raise ValueError("Expecting string")
            if self.no_semantic_versioning:
                return packaging.version.Version(version)
            return semantic_version.Version(version)
        except ValueError as exc:
            self.errors.append(
                (
                    self.path,
                    0,
                    0,
                    "{0}: error while parse version {1!r}: {2}".format(
                        message, version, exc
                    ),
                )
            )
            return None

    def check_extra_entries(
        self, data: dict, allowed_keys: set[str], yaml_path: list[Any]
    ) -> None:
        """
        Verify that no extra keys than the ones from ``allowed_keys`` appear in ``data``.
        """
        if not self.strict:
            return
        for key in data:
            if key not in allowed_keys:
                self.errors.append(
                    (
                        self.path,
                        0,
                        0,
                        "{0}: extra key not allowed".format(
                            self._format_yaml_path(yaml_path + [key]),
                        ),
                    )
                )

    @staticmethod
    def _format_yaml_path(yaml_path: list[Any]) -> str:
        """
        Format path to YAML element as string.
        """
        return "{0}".format(" -> ".join([repr(component) for component in yaml_path]))

    def verify_type(
        self,
        value: Any,
        allowed_types: tuple[type[Any], ...],
        yaml_path: list[Any],
        allow_none=False,
    ) -> bool:
        """
        Verify that a value is of a given type.

        :arg value: Value to check
        :arg allowed_types: Tuple with allowed types
        :arg yaml_path: Path to this object in the YAML file
        :arg allow_none: Whether ``None`` is an acceptable value
        """
        if allow_none and value is None:
            return True

        if isinstance(value, allowed_types):
            return True

        if len(allowed_types) == 1:
            allowed_types_str = "{0}".format(str(allowed_types[0]))
        else:
            allowed_types_str = "one of {0}".format(
                ", ".join([str(allowed_type) for allowed_type in allowed_types])
            )
        if allow_none:
            allowed_types_str = "null or {0}".format(allowed_types_str)
        self.errors.append(
            (
                self.path,
                0,
                0,
                "{0} is expected to be {1}, but got {2!r}".format(
                    self._format_yaml_path(yaml_path),
                    allowed_types_str,
                    value,
                ),
            )
        )
        return False

    def verify_plugin(
        self, plugin: dict, yaml_path: list[Any], is_module: bool
    ) -> None:
        """
        Verify that a given dictionary is a plugin or module description.

        :arg plugin: The dictionary to check
        :arg yaml_path: Path to this dictionary in the YAML
        :arg is_module: Whether this is a module description or a plugin description
        """
        if self.verify_type(plugin, (dict,), yaml_path):
            name = plugin.get("name")
            if self.verify_type(name, (str,), yaml_path + ["name"]):
                name = cast(str, name)
                if "." in name:
                    self.errors.append(
                        (
                            self.path,
                            0,
                            0,
                            "{0} must not be a FQCN".format(
                                self._format_yaml_path(yaml_path + ["name"])
                            ),
                        )
                    )
            self.verify_type(
                plugin.get("description"), (str,), yaml_path + ["description"]
            )
            namespace = plugin.get("namespace")
            if is_module:
                if self.verify_type(namespace, (str,), yaml_path + ["namespace"]):
                    namespace = cast(str, namespace)
                    if " " in namespace or "/" in namespace or "\\" in namespace:
                        self.errors.append(
                            (
                                self.path,
                                0,
                                0,
                                "{0} must not contain spaces or "
                                "slashes".format(
                                    self._format_yaml_path(yaml_path + ["namespace"])
                                ),
                            )
                        )
            else:
                if namespace is not None:
                    self.errors.append(
                        (
                            self.path,
                            0,
                            0,
                            "{0} must be null".format(
                                self._format_yaml_path(yaml_path + ["namespace"])
                            ),
                        )
                    )
            self.check_extra_entries(
                plugin,
                {
                    "release_date",
                    "name",
                    "description",
                    "namespace",
                },
                yaml_path,
            )

    def lint_plugins(self, version_str: str, plugins_dict: dict):
        """
        Lint a plugin dictionary.

        :arg version_str: To which release the plugin dictionary belongs
        :arg plugins_dict: The plugin dictionary
        """
        for plugin_type, plugins in plugins_dict.items():
            if self.verify_type(
                plugin_type, (str,), ["releases", version_str, "plugins"]
            ):
                if plugin_type not in self.valid_plugin_types:
                    self.errors.append(
                        (
                            self.path,
                            0,
                            0,
                            "Unknown plugin type {0!r} in {1}".format(
                                plugin_type,
                                self._format_yaml_path(
                                    ["releases", version_str, "plugins"]
                                ),
                            ),
                        )
                    )
            if self.verify_type(
                plugins, (list,), ["releases", version_str, "plugins", plugin_type]
            ):
                for idx, plugin in enumerate(plugins):
                    self.verify_plugin(
                        plugin,
                        ["releases", version_str, "plugins", plugin_type, idx],
                        is_module=False,
                    )

    def lint_objects(self, version_str: str, objects_dict: dict):
        """
        Lint a object dictionary.

        :arg version_str: To which release the object dictionary belongs
        :arg objects_dict: The object dictionary
        """
        for object_type, objects in objects_dict.items():
            if self.verify_type(
                object_type, (str,), ["releases", version_str, "objects"]
            ):
                if object_type not in OBJECT_TYPES:
                    self.errors.append(
                        (
                            self.path,
                            0,
                            0,
                            "Unknown object type {0!r} in {1}".format(
                                object_type,
                                self._format_yaml_path(
                                    ["releases", version_str, "objects"]
                                ),
                            ),
                        )
                    )
            if self.verify_type(
                objects, (list,), ["releases", version_str, "objects", object_type]
            ):
                for idx, ansible_object in enumerate(objects):
                    self.verify_plugin(
                        ansible_object,
                        ["releases", version_str, "objects", object_type, idx],
                        is_module=False,
                    )

    def lint_changes(
        self, fragment_linter: ChangelogFragmentLinter, version_str: str, changes: dict
    ):
        """
        Lint changes for an entry of the releases list.

        :arg fragment_linter: A fragment linter
        :arg version_str: The version the changes belongs to
        :arg entry: The changes dictionary
        """
        fragment = ChangelogFragment.from_dict(changes, self.path)
        for error in fragment_linter.lint(fragment):
            self.errors.append(
                (
                    error[0],
                    error[1],
                    error[2],
                    "{1}: {0}".format(
                        error[3],
                        self._format_yaml_path(["releases", version_str, "changes"]),
                    ),
                )
            )

    def lint_releases_entry(
        self, fragment_linter: ChangelogFragmentLinter, version_str: str, entry: dict
    ):
        """
        Lint an entry of the releases list.

        :arg fragment_linter: A fragment linter
        :arg version_str: The version this entry belongs to
        :arg entry: The releases list entry
        """
        release_date = entry.get("release_date")
        if self.verify_type(
            release_date, (str,), ["releases", version_str, "release_date"]
        ):
            release_date = cast(str, release_date)
            if not ISO_DATE_REGEX.match(release_date):
                self.errors.append(
                    (
                        self.path,
                        0,
                        0,
                        "{0} must be a ISO date (YYYY-MM-DD)".format(
                            self._format_yaml_path(
                                ["releases", version_str, "release_date"]
                            )
                        ),
                    )
                )

        codename = entry.get("codename")
        self.verify_type(
            codename, (str,), ["releases", version_str, "codename"], allow_none=True
        )

        changes = entry.get("changes")
        if (
            self.verify_type(
                changes, (dict,), ["releases", version_str, "changes"], allow_none=True
            )
            and changes
        ):
            self.lint_changes(fragment_linter, version_str, cast(dict, changes))

        modules = entry.get("modules")
        if (
            self.verify_type(
                modules, (list,), ["releases", version_str, "modules"], allow_none=True
            )
            and modules
        ):
            modules = cast(list, modules)
            for idx, module in enumerate(modules):
                self.verify_plugin(
                    module, ["releases", version_str, "modules", idx], is_module=True
                )

        plugins = entry.get("plugins")
        if (
            self.verify_type(
                plugins, (dict,), ["releases", version_str, "plugins"], allow_none=True
            )
            and plugins
        ):
            plugins = cast(dict, plugins)
            self.lint_plugins(version_str, plugins)

        objects = entry.get("objects")
        if (
            self.verify_type(
                objects, (dict,), ["releases", version_str, "objects"], allow_none=True
            )
            and objects
        ):
            objects = cast(dict, objects)
            self.lint_objects(version_str, objects)

        fragments = entry.get("fragments")
        if (
            self.verify_type(
                fragments,
                (list,),
                ["releases", version_str, "fragments"],
                allow_none=True,
            )
            and fragments
        ):
            fragments = cast(list, fragments)
            for idx, fragment in enumerate(fragments):
                self.verify_type(
                    fragment, (str,), ["releases", version_str, "fragments", idx]
                )

        self.check_extra_entries(
            entry,
            {
                "release_date",
                "codename",
                "changes",
                "modules",
                "plugins",
                "objects",
                "fragments",
            },
            ["releases", version_str],
        )

    def lint_content(self, changelog_yaml: dict) -> None:
        """
        Lint the contents of a changelog.yaml file, provided it is a global mapping.
        """
        ancestor_str = changelog_yaml.get("ancestor")
        if ancestor_str is not None:
            ancestor = self.check_version(ancestor_str, "Invalid ancestor version")
        else:
            ancestor = None

        paths = PathsConfig.force_collection("")  # path doesn't matter
        config = ChangelogConfig.default(paths, CollectionDetails(paths))
        fragment_linter = ChangelogFragmentLinter(config)

        if self.verify_type(changelog_yaml.get("releases"), (dict,), ["releases"]):
            for version_str, entry in changelog_yaml["releases"].items():
                # Check version
                version = self.check_version(version_str, "Invalid release version")
                if version is not None and ancestor is not None:
                    if version <= ancestor:
                        self.errors.append(
                            (
                                self.path,
                                0,
                                0,
                                "release version {0!r} must come after ancestor "
                                "version {1!r}".format(version_str, ancestor_str),
                            )
                        )

                # Check release information
                if self.verify_type(entry, (dict,), ["releases", version_str]):
                    self.lint_releases_entry(fragment_linter, version_str, entry)

        self.check_extra_entries(changelog_yaml, {"releases", "ancestor"}, [])

    def lint(self) -> list[tuple[str, int, int, str]]:
        """
        Load and lint the changelog.yaml file.
        """
        try:
            changelog_yaml = load_yaml_file(self.path)
        except Exception as exc:  # pylint: disable=broad-except
            self.errors.append(
                (
                    self.path,
                    0,
                    0,
                    "error while parsing YAML: {0}".format(exc).replace("\n", " "),
                )
            )
            return self.errors

        if not isinstance(changelog_yaml, dict):
            self.errors.append(
                (
                    self.path,
                    0,
                    0,
                    "YAML file is not a global mapping",
                )
            )
            return self.errors

        if self.preprocess_data:
            self.preprocess_data(changelog_yaml)

        self.lint_content(changelog_yaml)
        return self.errors


def lint_changelog_yaml(
    path: str,
    *,
    no_semantic_versioning: bool = False,
    preprocess_data: Callable[[dict], None] | None = None,
    strict: bool = False,
) -> list[tuple[str, int, int, str]]:
    """
    Lint a changelogs/changelog.yaml file.

    :kwarg no_semantic_versioning: Set to ``True`` if the file does not use
        semantic versioning, but Python version numbers.
    :kwarg preprocess_data: If provided, will be called on the data loaded before
        it is checked. This can be used to remove extra data before validation.
    :kwarg strict: Set to ``True`` to enable more strict validation
        (complain about extra fields).
    """
    return ChangelogYamlLinter(
        path,
        no_semantic_versioning=no_semantic_versioning,
        preprocess_data=preprocess_data,
        strict=strict,
    ).lint()

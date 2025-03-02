# Author: Matt Clay <matt@mystile.com>
# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Configuration classes for paths and changelogs.
"""

from __future__ import annotations

import enum
import os
import typing as t
from collections.abc import Mapping
from collections.abc import Sequence as _Sequence

import pydantic as p
from antsibull_fileutils.yaml import load_yaml_file, store_yaml_file

from .errors import ChangelogError
from .logger import LOGGER


def _is_sequence(value: t.Any) -> bool:
    if not isinstance(value, _Sequence):
        return False
    return not isinstance(value, (str, bytes))


def _ordinal(index: int) -> str:
    one = abs(index) % 10
    if one == 1:
        return f"{index}st"
    if one == 2:
        return f"{index}nd"
    if one == 3:
        return f"{index}rd"
    return f"{index}th"


class TextFormat(enum.Enum):
    """
    Supported text formats.
    """

    RESTRUCTURED_TEXT = "restructuredtext"
    MARKDOWN = "markdown"

    def to_extension(self) -> str:
        """
        Convert a text format to the associated extension (without leading dot).
        """
        if self == TextFormat.RESTRUCTURED_TEXT:
            return "rst"
        if self == TextFormat.MARKDOWN:
            return "md"
        raise ValueError(f"Unknown text format {self}")  # pragma: no cover

    @staticmethod
    def from_extension(extension: str) -> TextFormat:
        """
        Convert a file extension (without leading dot) to the corresponding text format.
        """
        if extension == "rst":
            return TextFormat.RESTRUCTURED_TEXT
        if extension == "md":
            return TextFormat.MARKDOWN
        raise ValueError(f"Unknown extension {extension!r}")


def _is_other_project_config(config_path: str) -> bool:
    try:
        config = load_yaml_file(config_path)
        return config.get("is_other_project", False)
    except:  # pylint: disable=bare-except;  # noqa: E722
        return False


class PathsConfig:
    """
    Configuration for paths.
    """

    is_collection: bool
    is_other_project: bool

    base_dir: str
    galaxy_path: str | None
    changelog_dir: str
    config_path: str
    ansible_doc_path: str

    @staticmethod
    def _changelog_dir(base_dir: str) -> str:
        return os.path.join(base_dir, "changelogs")

    @staticmethod
    def _config_path(changelog_dir: str) -> str:
        return os.path.join(changelog_dir, "config.yaml")

    def __init__(
        self,
        is_collection: bool,
        base_dir: str,
        galaxy_path: str | None,
        ansible_doc_path: str | None,
        is_other_project: bool = False,
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
        if (
            not self.is_other_project
            and galaxy_path
            and not os.path.exists(galaxy_path)
        ):
            LOGGER.debug("Cannot find galaxy.yml")
            galaxy_path = None
        self.galaxy_path = galaxy_path
        self.changelog_dir = PathsConfig._changelog_dir(self.base_dir)
        self.config_path = PathsConfig._config_path(self.changelog_dir)
        self.ansible_doc_path = ansible_doc_path or "ansible-doc"

    @staticmethod
    def force_collection(
        base_dir: str, ansible_doc_bin: str | None = None
    ) -> "PathsConfig":
        """
        Forces configuration for collection checkout with given base path.

        :arg base_dir: Base directory of collection checkout
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(
            True, base_dir, os.path.join(base_dir, "galaxy.yml"), ansible_doc_bin
        )

    @staticmethod
    def force_ansible(
        base_dir: str, ansible_doc_bin: str | None = None
    ) -> "PathsConfig":
        """
        Forces configuration with given ansible-core/-base base path.

        :type base_dir: Base directory of ansible-core/-base checkout
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(False, base_dir, None, ansible_doc_bin)

    @staticmethod
    def force_other(base_dir: str, ansible_doc_bin: str | None = None) -> "PathsConfig":
        """
        Forces configuration for a project that's neither ansible-core/-base nor an
        Ansible collection.

        :type base_dir: Base directory of the project
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        base_dir = os.path.abspath(base_dir)
        return PathsConfig(
            False, base_dir, None, ansible_doc_bin, is_other_project=True
        )

    @staticmethod
    def detect(
        is_collection: bool | None = None,
        ansible_doc_bin: str | None = None,
        is_other_project: bool | None = None,
        fallback_to_other_project: bool = False,
    ) -> "PathsConfig":
        """
        Detect paths configuration from current working directory.

        :raises ChangelogError: cannot identify collection, ansible-core/-base checkout,
                                or other project.
        :arg ansible_doc_bin: Override path to ansible-doc.
        """
        previous: str | None = None
        base_dir = os.getcwd()
        while True:
            changelog_dir = PathsConfig._changelog_dir(base_dir)
            config_path = PathsConfig._config_path(changelog_dir)
            if os.path.exists(changelog_dir) and os.path.exists(config_path):
                if is_other_project is True or (
                    not is_collection and _is_other_project_config(config_path)
                ):
                    # This is neither ansible-core/-base nor an Ansible collection,
                    # but explicitly marked as an 'other project'
                    return PathsConfig(
                        False, base_dir, None, ansible_doc_bin, is_other_project=True
                    )
                galaxy_path = os.path.join(base_dir, "galaxy.yml")
                if os.path.exists(galaxy_path) or is_collection is True:
                    # We are in a collection and assume ansible-doc is available in $PATH
                    return PathsConfig(True, base_dir, galaxy_path, ansible_doc_bin)
                ansible_lib_dir = os.path.join(base_dir, "lib", "ansible")
                if os.path.exists(ansible_lib_dir) or is_collection is False:
                    # We are in a checkout of ansible/ansible
                    return PathsConfig(False, base_dir, None, ansible_doc_bin)
                if fallback_to_other_project:
                    # Fallback to other project
                    return PathsConfig(
                        False, base_dir, None, ansible_doc_bin, is_other_project=True
                    )
            previous, base_dir = base_dir, os.path.dirname(base_dir)
            if previous in (
                base_dir,
                os.environ.get("__ANTSIBULL_CHANGELOG_CI_ROOT", base_dir),
            ):
                raise ChangelogError(
                    "Cannot identify collection, ansible-core/-base"
                    " checkout, or other project."
                )


def load_galaxy_metadata(paths: PathsConfig) -> dict:
    """
    Load galaxy.yml metadata.

    :arg paths: Paths configuration.
    :return: The contents of ``galaxy.yml``.
    """
    path = paths.galaxy_path
    if path is None:
        raise ChangelogError("Cannot find galaxy.yml")
    return load_yaml_file(path)


class CollectionDetails:
    """
    Stores information about a collection. Can auto-populate from galaxy.yml.
    """

    paths: PathsConfig
    galaxy_yaml_loaded: bool

    namespace: str | None
    name: str | None
    version: str | None
    flatmap: bool | None

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
            raise ChangelogError("galaxy.yml must be a dictionary")
        if self.namespace is None and isinstance(galaxy_yaml.get("namespace"), str):
            self.namespace = galaxy_yaml.get("namespace")
        if self.name is None and isinstance(galaxy_yaml.get("name"), str):
            self.name = galaxy_yaml.get("name")
        if self.version is None and isinstance(galaxy_yaml.get("version"), str):
            self.version = galaxy_yaml.get("version")
        if self.flatmap is None and galaxy_yaml.get("type") is not None:
            self.flatmap = galaxy_yaml["type"] == "flatmap"

    def _load_galaxy_yaml(
        self, needed_var: str, what_for: str | None = None, help_text: str | None = None
    ):
        if self.galaxy_yaml_loaded:
            return
        if not self.paths.is_collection:
            raise RuntimeError(
                "Internal error: cannot get collection details for non-collection"
            )

        if what_for is None:
            what_for = f'load field "{needed_var}"'
        try:
            galaxy_yaml = load_galaxy_metadata(self.paths)
        except Exception as exc:
            msg = f"Cannot find galaxy.yml to {what_for}: {exc}"
            if help_text is not None:
                msg = f"{msg}. {help_text}"
            raise ChangelogError(msg) from exc

        self._parse_galaxy_yaml(galaxy_yaml)

    def get_namespace(self) -> str:
        """
        Get collection's namespace.
        """
        help_text = (
            "You can explicitly specify the value with `--collection-namespace`."
        )
        if self.namespace is None:
            self._load_galaxy_yaml("namespace", help_text=help_text)
        namespace = self.namespace
        if namespace is None:
            raise ChangelogError(
                'Cannot find "namespace" field in galaxy.yml. ' + help_text
            )
        return namespace

    def get_name(self) -> str:
        """
        Get collection's name.
        """
        help_text = "You can explicitly specify the value with `--collection-name`."
        if self.name is None:
            self._load_galaxy_yaml("name", help_text=help_text)
        name = self.name
        if name is None:
            raise ChangelogError('Cannot find "name" field in galaxy.yml. ' + help_text)
        return name

    def get_version(self) -> str:
        """
        Get collection's version.
        """
        help_text = "You can explicitly specify the value with `--version`."
        if self.version is None:
            self._load_galaxy_yaml("version", help_text=help_text)
        version = self.version
        if version is None:
            raise ChangelogError(
                'Cannot find "version" field in galaxy.yml. ' + help_text
            )
        return version

    def get_flatmap(self) -> bool | None:
        """
        Get collection's flatmap flag.
        """
        help_text = "You can explicitly specify the value with `--collection-flatmap`."
        if self.flatmap is None and not self.galaxy_yaml_loaded:
            self._load_galaxy_yaml(
                "type", what_for="determine flatmapping", help_text=help_text
            )
        return self.flatmap


DEFAULT_SECTIONS = [
    ["major_changes", "Major Changes"],
    ["minor_changes", "Minor Changes"],
    ["breaking_changes", "Breaking Changes / Porting Guide"],
    ["deprecated_features", "Deprecated Features"],
    ["removed_features", "Removed Features (previously deprecated)"],
    ["security_fixes", "Security Fixes"],
    ["bugfixes", "Bugfixes"],
    ["known_issues", "Known Issues"],
]


class ChangelogConfig(p.BaseModel):
    """
    Configuration for changelogs.
    """

    model_config = p.ConfigDict(
        frozen=False, extra="allow", validate_default=True, arbitrary_types_allowed=True
    )

    paths: PathsConfig
    collection_details: CollectionDetails
    is_collection: bool
    config: dict

    title: t.Optional[str] = None
    notes_dir: str = p.Field(default="fragments", alias="notesdir")
    prelude_name: str = p.Field(default="release_summary", alias="prelude_section_name")
    prelude_title: str = p.Field(
        default="Release Summary", alias="prelude_section_title"
    )
    new_plugins_after_name: str = ""  # not used
    changes_file: str = ".changes.yaml"
    changes_format: t.Literal["combined"]
    keep_fragments: bool = False
    prevent_known_fragments: bool  # default is set in parse()
    use_fqcn: bool = False
    archive_path_template: t.Optional[str] = None
    changelog_filename_template: str = "CHANGELOG-v%s.rst"
    changelog_filename_version_depth: int = 2
    mention_ancestor: bool = True
    trivial_section_name: t.Optional[str]  # default is set by parse()
    release_tag_re: str = r"((?:[\d.ab]|rc)+)"  # only relevant for ansible-core
    pre_release_tag_re: str = (
        r"(?P<pre_release>\.\d+(?:[ab]|rc)+\d*)$"  # only relevant for ansible-core
    )
    always_refresh: str = "none"
    ignore_other_fragment_extensions: bool = False
    sanitize_changelog: bool = False
    flatmap: t.Optional[bool] = None
    use_semantic_versioning: bool = (
        True  # default is False for ansible-core and other projects
    )
    is_other_project: bool = False
    sections: Mapping[str, str] = dict(DEFAULT_SECTIONS)
    output_formats: set[TextFormat] = {TextFormat.RESTRUCTURED_TEXT}
    add_plugin_period: bool = False
    changelog_nice_yaml: bool = False
    changelog_sort: t.Literal[
        "unsorted",
        "version",
        "version_reversed",
        "alphanumerical",
    ] = "alphanumerical"
    vcs: t.Literal["none", "auto", "git"] = "none"

    @p.field_validator("always_refresh", mode="before")
    @classmethod
    def fix_always_refresh(cls, value: t.Any) -> str:
        """
        Validate and adjust the value of always_refresh.
        """
        if value is True:
            value = "full"
        elif value is False:
            value = "none"
        if not isinstance(value, str):
            raise ValueError(
                "If specified, always_refresh must be a boolean or a string"
            )
        if value not in {"full", "none"}:
            for part in value.split(","):
                part = part.strip()
                if part not in {
                    "plugins",
                    "plugins-without-removal",
                    "fragments",
                    "fragments-without-archives",
                }:
                    if part in {"full", "none"}:
                        raise ValueError(
                            f'The config value always_refresh must not contain "{part}"'
                            " together with other values"
                        )
                    raise ValueError(
                        f'The config value always_refresh contains an invalid value "{part}"'
                    )
        return value

    @p.field_validator("sections", mode="before")
    @classmethod
    def parse_sections(cls, value: t.Any) -> Mapping[str, str]:
        """
        Parse the value of sections.
        """
        if isinstance(value, Mapping):
            for k, v in value.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    raise ValueError(
                        "The config value sections must be a dictionary mapping strings to strings"
                    )
            return value
        if not _is_sequence(value):
            raise ValueError("The config value sections must be a list")
        sections = {}
        for index, entry in enumerate(value):
            if not _is_sequence(entry) or len(entry) != 2:
                raise ValueError(
                    f"The {_ordinal(index + 1)} entry of config value sections"
                    " must be a list of length 2"
                )
            if not isinstance(entry[0], str):
                raise ValueError(
                    f"The {_ordinal(index + 1)} entry of config value sections"
                    " does not have a string as the first element"
                )
            if not isinstance(entry[1], str):
                raise ValueError(
                    f"The {_ordinal(index + 1)} entry of config value sections"
                    " does not have a string as the second element"
                )
            if entry[0] in sections:
                raise ValueError(
                    f"The section name {entry[0]!r} appears more than once"
                )
            sections[entry[0]] = entry[1]
        return sections

    @p.field_validator("output_formats", mode="before")
    @classmethod
    def parse_output_formats(cls, value: t.Any) -> set[TextFormat]:
        """
        Parse the value of output_formats.
        """
        if isinstance(value, set):
            for entry in value:
                if not isinstance(entry, TextFormat):
                    raise ValueError("The config value output_formats must be a list")
            return value
        if not _is_sequence(value):
            raise ValueError("The config value output_formats must be a list")
        result: set[TextFormat] = set()
        for index, entry in enumerate(value):
            if not isinstance(entry, str):
                raise ValueError(
                    f"The {_ordinal(index + 1)} entry of config value output_formats"
                    " is not a string"
                )
            try:
                text_format = TextFormat.from_extension(entry)
            except ValueError as exc:
                raise ValueError(
                    f"The {_ordinal(index + 1)} entry of config value output_formats"
                    f" is an unknown extension: {exc}"
                ) from exc
            if text_format in result:
                raise ValueError(f"The output format {entry!r} appears more than once")
            result.add(text_format)
        return result

    @p.model_validator(mode="after")
    def postprocess_sections(self) -> t.Self:
        """
        Postprocess sections value by inserting the prelude section.
        """
        sections = {self.prelude_name: self.prelude_title}
        for k, v in self.sections.items():
            if k == self.prelude_name:
                raise ValueError(
                    f"No section name must equal prelude_name ({self.prelude_name!r})"
                )
            sections[k] = v
        self.sections = sections
        return self

    @p.model_validator(mode="after")
    def validate_use_semantic_versioning(self) -> t.Self:
        """
        Validate use_semantic_versioning for collections.
        """
        if self.is_collection and not self.use_semantic_versioning:
            raise ValueError(
                "The config value use_semantic_versioning must be true for collections"
            )
        return self

    def _validate_other_project(self) -> None:
        """
        Basic config validation.
        """
        if self.is_other_project and self.is_collection:
            raise ChangelogError("is_other_project must not be true for collections")
        if self.is_other_project != self.paths.is_other_project:
            raise ChangelogError(f"is_other_project must be {self.is_other_project}")

    @classmethod
    def parse(
        cls,
        paths: PathsConfig,
        collection_details: CollectionDetails,
        config: dict,
        *,
        ignore_is_other_project: bool = False,
    ) -> ChangelogConfig:
        """
        Parse a raw changelog configuration.
        """
        adjusted_config = config.copy()
        adjusted_config["paths"] = paths
        adjusted_config["collection_details"] = collection_details
        adjusted_config["is_collection"] = paths.is_collection
        adjusted_config["config"] = config

        # Set some special defaults
        if "trivial_section_name" not in adjusted_config:
            adjusted_config["trivial_section_name"] = (
                "trivial" if (paths.is_collection or paths.is_other_project) else None
            )
        if "use_semantic_versioning" not in adjusted_config and not paths.is_collection:
            adjusted_config["use_semantic_versioning"] = False
        if "prevent_known_fragments" not in adjusted_config:
            adjusted_config["prevent_known_fragments"] = adjusted_config.get(
                "keep_fragments", False
            )

        # Parse
        try:
            result = cls.model_validate(adjusted_config)
        except Exception as exc:
            raise ChangelogError(f"Error while parsing changlog config: {exc}") from exc

        if not ignore_is_other_project:
            result._validate_other_project()  # pylint: disable=protected-access

        return result

    def store(self) -> None:  # noqa: C901
        """
        Store changelog configuration file to disk.
        """
        config: dict = {
            "notesdir": self.notes_dir,
            "changes_file": self.changes_file,
            "changes_format": self.changes_format,
            "mention_ancestor": self.mention_ancestor,
            "keep_fragments": self.keep_fragments,
            "use_fqcn": self.use_fqcn,
            "changelog_filename_template": self.changelog_filename_template,
            "changelog_filename_version_depth": self.changelog_filename_version_depth,
            "prelude_section_name": self.prelude_name,
            "prelude_section_title": self.prelude_title,
            "new_plugins_after_name": self.new_plugins_after_name,
            "trivial_section_name": self.trivial_section_name,
            "ignore_other_fragment_extensions": self.ignore_other_fragment_extensions,
            "sanitize_changelog": self.sanitize_changelog,
            "add_plugin_period": self.add_plugin_period,
            "changelog_nice_yaml": self.changelog_nice_yaml,
            "changelog_sort": self.changelog_sort,
            "vcs": self.vcs,
        }
        if not self.is_collection:
            if self.use_semantic_versioning:
                config["use_semantic_versioning"] = True
            else:
                config.update(
                    {
                        "release_tag_re": self.release_tag_re,
                        "pre_release_tag_re": self.pre_release_tag_re,
                    }
                )
        if self.title is not None:
            config["title"] = self.title
        if self.always_refresh != "none":
            config["always_refresh"] = self.always_refresh
        if self.keep_fragments != self.prevent_known_fragments:
            config["prevent_known_fragments"] = self.prevent_known_fragments
        if self.flatmap is not None:
            config["flatmap"] = self.flatmap
        if self.archive_path_template is not None:
            config["archive_path_template"] = self.archive_path_template
        if self.is_other_project:
            config["is_other_project"] = self.is_other_project

        sections = []
        for key, value in self.sections.items():
            if key == self.prelude_name and value == self.prelude_title:
                continue
            sections.append([key, value])
        config["sections"] = sections

        config["output_formats"] = sorted(
            text_format.to_extension() for text_format in self.output_formats
        )

        store_yaml_file(self.paths.config_path, config)

    @staticmethod
    def load(
        paths: PathsConfig,
        collection_details: CollectionDetails,
        ignore_is_other_project: bool = False,
    ) -> "ChangelogConfig":
        """
        Load changelog configuration file from disk.
        """
        config = load_yaml_file(paths.config_path)
        if not isinstance(config, dict):
            raise ChangelogError(f"{paths.config_path} must be a dictionary")
        return ChangelogConfig.parse(
            paths,
            collection_details,
            config,
            ignore_is_other_project=ignore_is_other_project,
        )

    @staticmethod
    def default(
        paths: PathsConfig,
        collection_details: CollectionDetails,
        title: str | None = None,
    ) -> "ChangelogConfig":
        """
        Create default changelog config.

        :type title: Title of the project
        """
        config = {
            "changes_file": "changelog.yaml",
            "changes_format": "combined",
            "changelog_filename_template": "../CHANGELOG.rst",
            "changelog_filename_version_depth": 0,
            "new_plugins_after_name": "removed_features",
            "sections": DEFAULT_SECTIONS,
            "use_fqcn": True,
            "ignore_other_fragment_extensions": True,
            "sanitize_changelog": True,
            "add_plugin_period": True,
            "changelog_nice_yaml": False,
            "changelog_sort": "alphanumerical",
            "vcs": "auto",
        }
        if title is not None:
            config["title"] = title
        if paths.is_other_project:
            config["is_other_project"] = True
            config["use_semantic_versioning"] = True
        return ChangelogConfig.parse(paths, collection_details, config)

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test config module.
"""

from __future__ import annotations

import os
import re

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.errors import ChangelogError


@pytest.fixture
def root():
    old_cwd = os.getcwd()
    try:
        os.chdir("/")
        yield
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def cwd_tmp_path(tmp_path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def ansible_config_path(tmp_path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        d = tmp_path / "lib"
        d.mkdir()
        d = d / "ansible"
        d.mkdir()
        d = tmp_path / "changelogs"
        d.mkdir()
        yield d / "config.yaml"
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def collection_config_path(tmp_path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / "galaxy.yml").write_text("")
        d = tmp_path / "changelogs"
        d.mkdir()
        yield d / "config.yaml"
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def other_config_path(tmp_path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        d = tmp_path / "changelogs"
        d.mkdir()
        yield d / "config.yaml"
    finally:
        os.chdir(old_cwd)


def test_detect_complete_fail(root):
    with pytest.raises(ChangelogError):
        PathsConfig.detect()


def test_detect_ansible_doc_binary(cwd_tmp_path):
    d = cwd_tmp_path / "lib"
    d.mkdir()
    d = d / "ansible"
    d.mkdir()
    d = cwd_tmp_path / "bin"
    d.mkdir()
    ansible_doc = d / "ansible-doc"
    ansible_doc.write_text("#!/usr/bin/python")
    d = cwd_tmp_path / "changelogs"
    d.mkdir()
    (d / "config.yaml").write_text("---")
    c = PathsConfig.detect()
    assert c.is_other_project is False
    assert c.is_collection is False
    assert c.ansible_doc_path == "ansible-doc"


def test_detect_ansible_no_doc_binary(cwd_tmp_path):
    d = cwd_tmp_path / "lib"
    d.mkdir()
    d = d / "ansible"
    d.mkdir()
    d = cwd_tmp_path / "bin"
    d.mkdir()
    d = cwd_tmp_path / "changelogs"
    d.mkdir()
    (d / "config.yaml").write_text("---")
    c = PathsConfig.detect()
    assert c.is_other_project is False
    assert c.is_collection is False
    assert c.ansible_doc_path == "ansible-doc"


def test_detect_other(cwd_tmp_path):
    d = cwd_tmp_path / "lib"
    d.mkdir()
    d = d / "ansible"
    d.mkdir()
    d = cwd_tmp_path / "bin"
    d.mkdir()
    ansible_doc = d / "ansible-doc"
    ansible_doc.write_text("#!/usr/bin/python")
    (cwd_tmp_path / "galaxy.yml").write_text("")
    d = cwd_tmp_path / "changelogs"
    d.mkdir()
    (d / "config.yaml").write_text("is_other_project: true")
    c = PathsConfig.detect()
    assert c.is_other_project is True
    assert c.is_collection is False
    assert c.ansible_doc_path == "ansible-doc"


def test_config_loading_bad_changes_format(collection_config_path):
    collection_config_path.write_text("changes_format: other")
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(ChangelogError):
        ChangelogConfig.load(paths, collection_details)


def test_config_store_ansible(ansible_config_path):
    ansible_config_path.write_text("")
    paths = PathsConfig.detect()
    assert paths.is_collection is False
    assert paths.is_other_project is False
    collection_details = CollectionDetails(paths)

    config = ChangelogConfig.default(paths, collection_details)
    config.always_refresh = "none"
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"

    config.always_refresh = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"

    config.always_refresh = "full"
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"

    config.always_refresh = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"


def test_config_store_collection(collection_config_path):
    collection_config_path.write_text("")
    paths = PathsConfig.detect()
    assert paths.is_collection is True
    assert paths.is_other_project is False
    collection_details = CollectionDetails(paths)

    config = ChangelogConfig.default(paths, collection_details)
    assert config.flatmap is None

    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.flatmap is None

    config.always_refresh = "full"
    config.flatmap = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"
    assert config.flatmap is True

    config.always_refresh = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"
    assert config.flatmap is True

    config.always_refresh = "none"
    config.flatmap = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"
    assert config.flatmap is False

    config.always_refresh = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"
    assert config.flatmap is False


def test_config_store_other(other_config_path):
    other_config_path.write_text("is_other_project: true")
    paths = PathsConfig.detect()
    assert paths.is_collection is False
    assert paths.is_other_project is True
    collection_details = CollectionDetails(paths)

    config = ChangelogConfig.default(paths, collection_details)
    assert config.flatmap is None

    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.flatmap is None
    assert config.is_other_project is True

    config.always_refresh = "full"
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"
    assert config.is_other_project is True

    config.always_refresh = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "full"
    assert config.is_other_project is True

    config.always_refresh = "none"
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"
    assert config.is_other_project is True

    config.always_refresh = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh == "none"
    assert config.is_other_project is True


def test_collection_details(tmp_path):
    paths = PathsConfig.force_ansible(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(Exception) as exc:
        details.get_namespace()
    assert (
        str(exc.value)
        == "Internal error: cannot get collection details for non-collection"
    )
    with pytest.raises(Exception) as exc:
        details.get_name()
    assert (
        str(exc.value)
        == "Internal error: cannot get collection details for non-collection"
    )
    with pytest.raises(Exception) as exc:
        details.get_version()
    assert (
        str(exc.value)
        == "Internal error: cannot get collection details for non-collection"
    )
    with pytest.raises(Exception) as exc:
        details.get_flatmap()
    assert (
        str(exc.value)
        == "Internal error: cannot get collection details for non-collection"
    )

    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert "Cannot find galaxy.yml" in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert "Cannot find galaxy.yml" in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert "Cannot find galaxy.yml" in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_flatmap()
    assert "Cannot find galaxy.yml" in str(exc.value)

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\nfoo")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert "galaxy.yml must be a dictionary" in str(exc.value)

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\na: b\n")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert 'Cannot find "namespace" field in galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert 'Cannot find "name" field in galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert 'Cannot find "version" field in galaxy.yml' in str(exc.value)
    assert details.get_flatmap() is None

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\nnamespace: 1\nname: 2\nversion: 3\ntype: 4")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert 'Cannot find "namespace" field in galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert 'Cannot find "name" field in galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert 'Cannot find "version" field in galaxy.yml' in str(exc.value)
    assert details.get_flatmap() is False

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\nnamespace: a\nname: b\nversion: c\ntype: flatmap")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    assert details.get_namespace() == "a"
    assert details.get_name() == "b"
    assert details.get_version() == "c"
    assert details.get_flatmap() is True

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\ntype: other")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    assert details.get_flatmap() is False

    galaxy_path = tmp_path / "galaxy.yml"
    galaxy_path.write_text("---\nnamespace: a\nname: b\nversion: c\ntype: flatmap")
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    details.namespace = "test"
    details.name = "asdf"
    details.version = "1.0.0"
    details.flatmap = False
    assert details.get_namespace() == "test"
    assert details.get_name() == "asdf"
    assert details.get_version() == "1.0.0"
    assert details.get_flatmap() is False


def test_config_loading_bad_output_format(collection_config_path):
    collection_config_path.write_text("changes_format: combined\noutput_formats: 42")
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(
        ChangelogError,
        match="The config value output_formats must be a list",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text("changes_format: combined\noutput_formats:\n- 42")
    with pytest.raises(
        ChangelogError,
        match="The 1st entry of config value output_formats is not a string",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\noutput_formats: [rst, rst]"
    )
    with pytest.raises(
        ChangelogError,
        match="The output format 'rst' appears more than once",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\noutput_formats: [foobar]"
    )
    with pytest.raises(
        ChangelogError,
        match="The 1st entry of config value output_formats is an unknown extension: Unknown extension 'foobar'",
    ):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_bad_vcs(collection_config_path):
    collection_config_path.write_text("changes_format: combined\nvcs: foobar")
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(
        ChangelogError,
        match="Input should be 'none', 'auto' or 'git'",
    ):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_always_refresh(ansible_config_path):
    ansible_config_path.write_text(
        "changes_format: combined\nalways_refresh: plugins, fragments"
    )
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    config = ChangelogConfig.load(paths, collection_details)
    config.always_refresh == "plugins, fragments"

    ansible_config_path.write_text("changes_format: combined\nalways_refresh: 42")
    with pytest.raises(
        ChangelogError,
        match="If specified, always_refresh must be a boolean or a string",
    ):
        ChangelogConfig.load(paths, collection_details)

    ansible_config_path.write_text(
        "changes_format: combined\nalways_refresh: plugins, bar"
    )
    with pytest.raises(
        ChangelogError,
        match='The config value always_refresh contains an invalid value "bar"',
    ):
        ChangelogConfig.load(paths, collection_details)

    ansible_config_path.write_text(
        "changes_format: combined\nalways_refresh: plugins, full"
    )
    with pytest.raises(
        ChangelogError,
        match='The config value always_refresh must not contain "full" together with other values',
    ):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_bad_sections(collection_config_path):
    collection_config_path.write_text("changes_format: combined\nsections: 42")
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(
        ChangelogError,
        match="The config value sections must be a list",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text("changes_format: combined\nsections:\n  42: foo")
    with pytest.raises(
        ChangelogError,
        match="The config value sections must be a dictionary mapping strings to strings",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text("changes_format: combined\nsections:\n  foo: 42")
    with pytest.raises(
        ChangelogError,
        match="The config value sections must be a dictionary mapping strings to strings",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [foo, bar]\n- foo"
    )
    with pytest.raises(
        ChangelogError,
        match="The 2nd entry of config value sections must be a list of length 2",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [foo, bar]\n- [baz, bam]\n- [foo]"
    )
    with pytest.raises(
        ChangelogError,
        match="The 3rd entry of config value sections must be a list of length 2",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [foo, bar]\n- [baz, bam]\n- [bam, foo]\n- [1, foo]"
    )
    with pytest.raises(
        ChangelogError,
        match="The 4th entry of config value sections does not have a string as the first element",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [foo, bar]\n- [baz, bam]\n- [bam, foo]\n- [foo, 1]"
    )
    with pytest.raises(
        ChangelogError,
        match="The 4th entry of config value sections does not have a string as the second element",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [foo, bar]\n- [foo, baz]"
    )
    with pytest.raises(
        ChangelogError,
        match="The section name 'foo' appears more than once",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nsections:\n- [release_summary, foo]"
    )
    with pytest.raises(
        ChangelogError,
        match=re.escape("No section name must equal prelude_name ('release_summary')"),
    ):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_collection(collection_config_path):
    collection_config_path.write_text(
        "changes_format: combined\nuse_semantic_versioning: false"
    )
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(
        ChangelogError,
        match="The config value use_semantic_versioning must be true for collections",
    ):
        ChangelogConfig.load(paths, collection_details)

    collection_config_path.write_text(
        "changes_format: combined\nis_other_project: true"
    )
    with pytest.raises(
        ChangelogError,
        match="is_other_project must not be true for collections",
    ):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_bad_yaml(collection_config_path):
    collection_config_path.write_text("[]")
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(
        ChangelogError,
        match=" must be a dictionary",
    ):
        ChangelogConfig.load(paths, collection_details)

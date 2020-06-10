# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test config module.
"""

import os

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.errors import ChangelogError


@pytest.fixture
def root():
    old_cwd = os.getcwd()
    os.chdir('/')
    yield
    os.chdir(old_cwd)


@pytest.fixture
def cwd_tmp_path(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)


@pytest.fixture
def ansible_config_path(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    d = tmp_path / 'lib'
    d.mkdir()
    d = d / 'ansible'
    d.mkdir()
    d = tmp_path / 'changelogs'
    d.mkdir()
    yield d / 'config.yaml'
    os.chdir(old_cwd)


@pytest.fixture
def collection_config_path(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    (tmp_path / 'galaxy.yml').write_text('')
    d = tmp_path / 'changelogs'
    d.mkdir()
    yield d / 'config.yaml'
    os.chdir(old_cwd)


def test_detect_complete_fail(root):
    with pytest.raises(ChangelogError):
        PathsConfig.detect()


def test_detect_ansible_doc_binary(cwd_tmp_path):
    d = cwd_tmp_path / 'lib'
    d.mkdir()
    d = d / 'ansible'
    d.mkdir()
    d = cwd_tmp_path / 'bin'
    d.mkdir()
    ansible_doc = d / 'ansible-doc'
    ansible_doc.write_text('#!/usr/bin/python')
    d = cwd_tmp_path / 'changelogs'
    d.mkdir()
    (d / 'config.yaml').write_text('---')
    c = PathsConfig.detect()
    assert c.ansible_doc_path == 'ansible-doc'


def test_detect_ansible_no_doc_binary(cwd_tmp_path):
    d = cwd_tmp_path / 'lib'
    d.mkdir()
    d = d / 'ansible'
    d.mkdir()
    d = cwd_tmp_path / 'bin'
    d.mkdir()
    d = cwd_tmp_path / 'changelogs'
    d.mkdir()
    (d / 'config.yaml').write_text('---')
    c = PathsConfig.detect()
    assert c.ansible_doc_path == 'ansible-doc'


def test_config_loading_bad_changes_format(collection_config_path):
    collection_config_path.write_text('changes_format: other')
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(ChangelogError):
        ChangelogConfig.load(paths, collection_details)


def test_config_loading_bad_keep_fragments(ansible_config_path):
    ansible_config_path.write_text('changes_format: classic\nkeep_fragments: false')
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)
    with pytest.raises(ChangelogError):
        ChangelogConfig.load(paths, collection_details)


def test_config_store_ansible(ansible_config_path):
    ansible_config_path.write_text('')
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)

    config = ChangelogConfig.default(paths, collection_details)
    config.always_refresh = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh is False

    config.always_refresh = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh is True


def test_config_store_collection(collection_config_path):
    collection_config_path.write_text('')
    paths = PathsConfig.detect()
    collection_details = CollectionDetails(paths)

    config = ChangelogConfig.default(paths, collection_details)
    config.always_refresh = True
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh is True

    config.always_refresh = False
    config.store()
    config = ChangelogConfig.load(paths, collection_details)
    assert config.always_refresh is False


def test_collection_details(tmp_path):
    paths = PathsConfig.force_ansible(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(Exception) as exc:
        details.get_namespace()
    assert str(exc.value) == 'Internal error: cannot get collection details for non-collection'
    with pytest.raises(Exception) as exc:
        details.get_name()
    assert str(exc.value) == 'Internal error: cannot get collection details for non-collection'
    with pytest.raises(Exception) as exc:
        details.get_version()
    assert str(exc.value) == 'Internal error: cannot get collection details for non-collection'
    with pytest.raises(Exception) as exc:
        details.get_flatmap()
    assert str(exc.value) == 'Internal error: cannot get collection details for non-collection'

    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert 'Cannot find galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert 'Cannot find galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert 'Cannot find galaxy.yml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_flatmap()
    assert 'Cannot find galaxy.yml' in str(exc.value)

    galaxy_path = tmp_path / 'galaxy.yml'
    galaxy_path.write_text('---\na: b\n')
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert 'Cannot find "namespace" field in galaxy.yaml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert 'Cannot find "name" field in galaxy.yaml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert 'Cannot find "version" field in galaxy.yaml' in str(exc.value)
    assert details.get_flatmap() is False

    galaxy_path = tmp_path / 'galaxy.yml'
    galaxy_path.write_text('---\nnamespace: 1\nname: 2\nversion: 3\ntype: 4')
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    with pytest.raises(ChangelogError) as exc:
        details.get_namespace()
    assert 'Cannot find "namespace" field in galaxy.yaml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_name()
    assert 'Cannot find "name" field in galaxy.yaml' in str(exc.value)
    with pytest.raises(ChangelogError) as exc:
        details.get_version()
    assert 'Cannot find "version" field in galaxy.yaml' in str(exc.value)
    assert details.get_flatmap() is False

    galaxy_path = tmp_path / 'galaxy.yml'
    galaxy_path.write_text('---\nnamespace: a\nname: b\nversion: c\ntype: flatmap')
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    assert details.get_namespace() == 'a'
    assert details.get_name() == 'b'
    assert details.get_version() == 'c'
    assert details.get_flatmap() is True

    galaxy_path = tmp_path / 'galaxy.yml'
    galaxy_path.write_text('---\nnamespace: a\nname: b\nversion: c\ntype: flatmap')
    paths = PathsConfig.force_collection(str(tmp_path))
    details = CollectionDetails(paths)
    details.namespace = 'test'
    details.name = 'asdf'
    details.version = '1.0.0'
    details.flatmap = False
    assert details.get_namespace() == 'test'
    assert details.get_name() == 'asdf'
    assert details.get_version() == '1.0.0'
    assert details.get_flatmap() is False

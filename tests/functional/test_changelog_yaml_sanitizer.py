# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test changelog.yaml sanitizing.
"""

import glob
import json
import os.path
import re

import pytest

from antsibull_changelog.config import ChangelogConfig, CollectionDetails, PathsConfig
from antsibull_changelog.sanitize import sanitize_changes
from antsibull_changelog.yaml import load_yaml, store_yaml


# Set to True to generate sanitize files instead of using them
STORE_RESULT = False


# Collect files
PATTERNS = ['*.yml', '*.yaml']
BASE_DIR = os.path.dirname(__file__)
GOOD_TESTS = []
BAD_TESTS = []


def load_tests():
    for pattern in PATTERNS:
        for filename in glob.glob(os.path.join(BASE_DIR, 'good', pattern)):
            GOOD_TESTS.append(filename)
        for filename in glob.glob(os.path.join(BASE_DIR, 'bad', pattern)):
            json_filename = os.path.splitext(filename)[0] + '.json'
            if os.path.exists(json_filename):
                BAD_TESTS.append((filename, json_filename))
            else:
                pytest.fail('Missing {0} for {1}'.format(json_filename, filename))


load_tests()


# Test good files
@pytest.mark.parametrize('yaml_filename', GOOD_TESTS)
def test_good_changelog_yaml_files(yaml_filename):
    paths = PathsConfig.force_collection(base_dir='/')
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    data = load_yaml(yaml_filename)
    result = sanitize_changes(data, config)
    if 'ancestor' not in data and result['ancestor'] is None:
        result.pop('ancestor')
    assert result == data


@pytest.mark.parametrize('yaml_filename, json_filename', BAD_TESTS)
def test_bad_changelog_yaml_files(yaml_filename, json_filename):
    paths = PathsConfig.force_collection(base_dir='/')
    config = ChangelogConfig.default(paths, CollectionDetails(paths))
    try:
        data = load_yaml(yaml_filename)
        if not STORE_RESULT:
            sanitized_data = load_yaml(yaml_filename + '-sanitized')
    except Exception:
        # We are only interested in parsable YAML
        return
    result = sanitize_changes(data, config)
    if STORE_RESULT:
        store_yaml(yaml_filename + '-sanitized', result)
    else:
        assert result == sanitized_data

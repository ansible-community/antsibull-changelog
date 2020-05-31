# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Test changelog.yaml linting.
"""

import glob
import json
import os.path
import re

import pytest

from antsibull_changelog.lint import lint_changelog_yaml


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
    errors = lint_changelog_yaml(yaml_filename)
    assert len(errors) == 0


@pytest.mark.parametrize('yaml_filename, json_filename', BAD_TESTS)
def test_bad_changelog_yaml_files(yaml_filename, json_filename):
    errors = lint_changelog_yaml(yaml_filename)
    assert len(errors) > 0

    # Cut off path
    errors = [[error[1], error[2], error[3].replace(yaml_filename, 'input.yaml')] for error in errors]

    # Load expected errors
    with open(json_filename, 'r') as json_f:
        data = json.load(json_f)

    if errors != data['errors']:
        print(json.dumps(errors, indent=2))

    assert len(errors) == len(data['errors'])
    for error1, error2 in zip(errors, data['errors']):
        assert error1[0:2] == error2[0:2]
        assert re.match(error2[2], error1[2], flags=re.DOTALL) is not None

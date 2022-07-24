# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test changelog.yaml linting.
"""

import glob
import io
import json
import os.path
import re
import sys

from contextlib import redirect_stdout

import pytest

from antsibull_changelog.lint import lint_changelog_yaml
from antsibull_changelog.cli import command_lint_changelog_yaml


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


class Args:
    def __init__(self, changelog_yaml_path=None, no_semantic_versioning=False):
        self.changelog_yaml_path = changelog_yaml_path
        self.no_semantic_versioning = no_semantic_versioning


# Test good files
@pytest.mark.parametrize('yaml_filename', GOOD_TESTS)
def test_good_changelog_yaml_files(yaml_filename):
    # Run test directly against implementation
    errors = lint_changelog_yaml(yaml_filename)
    assert len(errors) == 0

    # Run test against CLI
    args = Args(changelog_yaml_path=yaml_filename)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        rc = command_lint_changelog_yaml(args)
    stdout_lines = stdout.getvalue().splitlines()
    assert stdout_lines == []
    assert rc == 0


@pytest.mark.parametrize('yaml_filename, json_filename', BAD_TESTS)
def test_bad_changelog_yaml_files(yaml_filename, json_filename):
    # Run test directly against implementation
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

    # Run test against CLI
    args = Args(changelog_yaml_path=yaml_filename)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        rc = command_lint_changelog_yaml(args)
    stdout_lines = stdout.getvalue().splitlines()
    assert len(stdout_lines) == len(data['errors'])
    expected_lines = sorted(['^input\\.yaml:%d:%d: %s' % (error[0], error[1], error[2]) for error in data['errors']])
    for line, expected in zip(stdout_lines, expected_lines):
        line = line.replace(yaml_filename, 'input.yaml')
        assert re.match(expected, line, flags=re.DOTALL) is not None
    assert rc == 3

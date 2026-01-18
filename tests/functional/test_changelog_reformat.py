# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test basic changelog functionality: Ansible collections
"""

from __future__ import annotations

import os
from unittest import mock

from fixtures import collection_changelog  # noqa: F401; pylint: disable=unused-variable
from fixtures import create_plugin

import antsibull_changelog.ansible  # noqa: F401; pylint: disable=unused-variable
from antsibull_changelog import constants as C
from antsibull_changelog.config import TextFormat


def test_reformat(  # pylint: disable=redefined-outer-name
    collection_changelog,
):  # noqa: F811
    collection_changelog.config.title = "Test Collection"
    collection_changelog.config.use_fqcn = False
    collection_changelog.config.changelog_sort = "unsorted"
    collection_changelog.set_config(collection_changelog.config)
    collection_changelog.add_file(
        "changelogs/changelog.yaml",
        """
releases:
  10.0.0:
    changes:
      release_summary: "Bar"
      breaking_changes:
        - "This is a change"
    release_date: "2024-06-19"
    objects:
      role:
        - name: foo
          namespace: null
          description: Bar
      playbook:
        - name: foo
          namespace: null
          description: Bar
  1.0.0:
    release_date: "2024-06-17"
    changes:
      release_summary: "Foo"
    bar: baz
  2.0.0:
    changes:
      release_summary: "Baz"
    release_date: "2024-06-18"
other stuff: foobar
""".encode("utf-8"),
    )

    assert (
        collection_changelog.run_tool("reformat", ["-v", "--is-collection=true"])
        == C.RC_SUCCESS
    )

    assert (
        collection_changelog.read_file("changelogs/changelog.yaml").decode("utf-8")
        == """ancestor: null
releases:
  10.0.0:
    changes:
      breaking_changes:
      - This is a change
      release_summary: Bar
    objects:
      playbook:
      - description: Bar
        name: foo
        namespace: null
      role:
      - description: Bar
        name: foo
        namespace: null
    release_date: '2024-06-19'
  1.0.0:
    changes:
      release_summary: Foo
    release_date: '2024-06-17'
  2.0.0:
    changes:
      release_summary: Baz
    release_date: '2024-06-18'
"""
    )

    collection_changelog.config.changelog_sort = "alphanumerical"
    collection_changelog.set_config(collection_changelog.config)

    assert (
        collection_changelog.run_tool("reformat", ["-v", "--is-collection=true"])
        == C.RC_SUCCESS
    )

    assert (
        collection_changelog.read_file("changelogs/changelog.yaml").decode("utf-8")
        == """ancestor: null
releases:
  1.0.0:
    changes:
      release_summary: Foo
    release_date: '2024-06-17'
  10.0.0:
    changes:
      breaking_changes:
      - This is a change
      release_summary: Bar
    objects:
      playbook:
      - description: Bar
        name: foo
        namespace: null
      role:
      - description: Bar
        name: foo
        namespace: null
    release_date: '2024-06-19'
  2.0.0:
    changes:
      release_summary: Baz
    release_date: '2024-06-18'
"""
    )

    collection_changelog.config.changelog_nice_yaml = True
    collection_changelog.set_config(collection_changelog.config)

    assert (
        collection_changelog.run_tool("reformat", ["-v", "--is-collection=true"])
        == C.RC_SUCCESS
    )

    assert (
        collection_changelog.read_file("changelogs/changelog.yaml").decode("utf-8")
        == """---
ancestor: null
releases:
  1.0.0:
    changes:
      release_summary: Foo
    release_date: '2024-06-17'
  10.0.0:
    changes:
      breaking_changes:
        - This is a change
      release_summary: Bar
    objects:
      playbook:
        - description: Bar
          name: foo
          namespace: null
      role:
        - description: Bar
          name: foo
          namespace: null
    release_date: '2024-06-19'
  2.0.0:
    changes:
      release_summary: Baz
    release_date: '2024-06-18'
"""
    )

    collection_changelog.config.changelog_sort = "version_reversed"
    collection_changelog.set_config(collection_changelog.config)

    assert (
        collection_changelog.run_tool("reformat", ["-v", "--is-collection=true"])
        == C.RC_SUCCESS
    )

    assert (
        collection_changelog.read_file("changelogs/changelog.yaml").decode("utf-8")
        == """---
ancestor: null
releases:
  10.0.0:
    changes:
      breaking_changes:
        - This is a change
      release_summary: Bar
    objects:
      playbook:
        - description: Bar
          name: foo
          namespace: null
      role:
        - description: Bar
          name: foo
          namespace: null
    release_date: '2024-06-19'
  2.0.0:
    changes:
      release_summary: Baz
    release_date: '2024-06-18'
  1.0.0:
    changes:
      release_summary: Foo
    release_date: '2024-06-17'
"""
    )

    collection_changelog.config.changelog_sort = "version"
    collection_changelog.set_config(collection_changelog.config)

    assert (
        collection_changelog.run_tool("reformat", ["-v", "--is-collection=true"])
        == C.RC_SUCCESS
    )

    assert (
        collection_changelog.read_file("changelogs/changelog.yaml").decode("utf-8")
        == """---
ancestor: null
releases:
  1.0.0:
    changes:
      release_summary: Foo
    release_date: '2024-06-17'
  2.0.0:
    changes:
      release_summary: Baz
    release_date: '2024-06-18'
  10.0.0:
    changes:
      breaking_changes:
        - This is a change
      release_summary: Bar
    objects:
      playbook:
        - description: Bar
          name: foo
          namespace: null
      role:
        - description: Bar
          name: foo
          namespace: null
    release_date: '2024-06-19'
"""
    )

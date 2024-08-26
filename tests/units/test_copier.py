# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test utils module.
"""

from __future__ import annotations

import pathlib
import subprocess
from unittest import mock

import pytest

from antsibull_changelog.copier import GitCopier


def test_git_copier(tmp_path_factory):
    directory: pathlib.Path = tmp_path_factory.mktemp("changelog-test")

    src_dir = directory / "src"
    src_dir.mkdir()
    (src_dir / "empty").touch()
    (src_dir / "link").symlink_to("empty")
    (src_dir / "dir").mkdir()
    (src_dir / "file").write_text("content", encoding="utf-8")
    (src_dir / "dir" / "binary_file").write_bytes(b"\x00\x01\x02")

    copier = GitCopier()

    def assert_same(a: pathlib.Path, b: pathlib.Path):
        if a.is_file():
            assert b.is_file()
            assert a.read_bytes() == b.read_bytes()
            return
        if a.is_dir():
            assert b.is_dir()
            return
        if a.is_symlink():
            assert b.is_symlink()
            assert a.readlink() == b.readlink()
            return

    dest_dir = directory / "dest1"
    with mock.patch(
        "subprocess.check_output",
        return_value="file\x00".encode("utf-8"),
    ) as m:
        copier.copy(str(src_dir), str(dest_dir))

        m.assert_called_with(
            [
                "git",
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--deduplicate",
            ],
            cwd=str(src_dir),
        )

        assert dest_dir.is_dir()
        assert {p.name for p in dest_dir.iterdir()} == {"file"}
        assert_same(src_dir / "file", dest_dir / "file")

    dest_dir = directory / "dest2"
    with mock.patch(
        "subprocess.check_output",
        return_value="link\x00foobar\x00dir/binary_file".encode("utf-8"),
    ) as m:
        copier.copy(str(src_dir), str(dest_dir))

        m.assert_called_with(
            [
                "git",
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--deduplicate",
            ],
            cwd=str(src_dir),
        )

        assert dest_dir.is_dir()
        assert {p.name for p in dest_dir.iterdir()} == {"link", "dir"}
        assert_same(src_dir / "link", dest_dir / "link")
        assert_same(src_dir / "dir", dest_dir / "dir")
        assert {p.name for p in (dest_dir / "dir").iterdir()} == {"binary_file"}
        assert_same(src_dir / "dir" / "binary_file", dest_dir / "dir" / "binary_file")

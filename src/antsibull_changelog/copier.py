# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Directory and collection copying helpers.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from .config import ChangelogConfig, PathsConfig
from .errors import ChangelogError
from .logger import LOGGER
from .utils import detect_vcs


class Copier:  # pylint: disable=too-few-public-methods
    """
    Allows to copy directories.
    """

    def copy(self, from_path: str, to_path: str) -> None:
        """
        Copy a directory ``from_path`` to a destination ``to_path``.

        ``to_path`` must not exist, but its parent directory must exist.
        """
        LOGGER.debug("Copying complete directory from {!r} to {!r}", from_path, to_path)
        shutil.copytree(from_path, to_path, symlinks=True)


class GitCopier(Copier):  # pylint: disable=too-few-public-methods
    """
    Allows to copy directories that are part of a Git repository.
    """

    def copy(self, from_path: str, to_path: str) -> None:
        LOGGER.debug("Identifying files not ignored by Git in {!r}", from_path)
        os.mkdir(to_path, mode=0o700)
        try:
            files = (
                subprocess.check_output(
                    [
                        "git",
                        "ls-files",
                        "-z",
                        "--cached",
                        "--others",
                        "--exclude-standard",
                        "--deduplicate",
                    ],
                    cwd=from_path,
                )
                .strip(b"\x00")
                .split(b"\x00")
            )
        except subprocess.CalledProcessError as exc:
            raise ChangelogError("Error while running git") from exc
        except FileNotFoundError as exc:
            raise ChangelogError("Cannot find git executable") from exc

        LOGGER.debug(
            "Copying {} file(s) from {!r} to {!r}", len(files), from_path, to_path
        )
        created_directories = set()
        for file in files:
            # Decode filename and check whether the file still exists
            # (deleted files are part of the output)
            file_decoded = file.decode("utf-8")
            src_path = os.path.join(from_path, file_decoded)
            if not os.path.exists(src_path):
                continue

            # Check whether the directory for this file exists
            directory, _ = os.path.split(file_decoded)
            if directory not in created_directories:
                os.makedirs(os.path.join(to_path, directory), mode=0o700, exist_ok=True)
                created_directories.add(directory)

            # Copy the file
            dst_path = os.path.join(to_path, file_decoded)
            shutil.copyfile(src_path, dst_path)


class CollectionCopier:
    """
    Creates a copy of a collection to a place where ``--playbook-dir`` can be used
    to prefer this copy of the collection over any installed ones.
    """

    def __init__(
        self, paths: PathsConfig, config: ChangelogConfig, namespace: str, name: str
    ):
        self.paths = paths
        self.namespace = namespace
        self.name = name
        self.copier = Copier()
        vcs = config.vcs
        if vcs == "auto":
            vcs = detect_vcs(self.paths.base_dir)
        if vcs == "git":
            self.copier = GitCopier()

        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="antsibull-changelog"))

    def __enter__(self) -> tuple[str, PathsConfig]:
        try:
            collection_container_dir = os.path.join(
                self.dir, "collections", "ansible_collections", self.namespace
            )
            os.makedirs(collection_container_dir)

            collection_dir = os.path.join(collection_container_dir, self.name)
            LOGGER.debug("Temporary collection directory: {!r}", collection_dir)

            self.copier.copy(self.paths.base_dir, collection_dir)

            LOGGER.debug("Temporary collection directory has been populated")
            new_paths = PathsConfig.force_collection(
                collection_dir, ansible_doc_bin=self.paths.ansible_doc_path
            )
            return self.dir, new_paths
        except Exception:
            shutil.rmtree(self.dir, ignore_errors=True)
            raise

    def __exit__(self, type_, value, traceback_):
        shutil.rmtree(self.dir, ignore_errors=True)

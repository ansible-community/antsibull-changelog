# Author: Sagar Paul <paul.sagar@yahoo.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2023, Ansible Project

"""
Update version in galaxy.yml.
"""

from __future__ import annotations

from os import PathLike

from .yaml import load_yaml, store_yaml


class UpdateGalaxy:
    """
    Load and update galaxy.yaml file.
    """

    galaxy_path: str | None
    version: str | None

    def __init__(self, galaxy_path: str, version: str):
        self.galaxy_path = galaxy_path
        self.version = version
        self.update_galaxy_file()

    def update_galaxy_file(self) -> None:
        """
        Load and update galaxy.yaml file.
        """
        config = load_yaml(self.galaxy_path)
        config["version"] = str(self.version)
        store_yaml(self.galaxy_path, config)

# Author: Sagar Paul <paul.sagar@yahoo.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2023, Ansible Project

"""
Update the galaxy the yaml file.
"""

from __future__ import annotations

# from typing import TYPE_CHECKING

from .logger import LOGGER
from .yaml import load_yaml, store_yaml

# if TYPE_CHECKING:
#     from _typeshed import StrOrBytesPath


def update_galaxy(galaxy_path: str, version: str) -> None:
    """
    Load and update galaxy.yaml file.
    """
    try:
        config = load_yaml(galaxy_path)

        if config["version"] == version:
            return
            config["version"] = version
            store_yaml(galaxy_path, config)

    except Exception:  # pylint: disable=broad-except
        LOGGER.error("Unable to load the galaxy.yml file.")

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test ansible module.
"""

from __future__ import annotations

import os

import pytest

from antsibull_changelog.ansible import get_ansible_release


def test_ansible_release():
    with pytest.raises(ValueError) as exc:
        get_ansible_release()
    assert str(exc.value) == "Cannot import ansible.release"

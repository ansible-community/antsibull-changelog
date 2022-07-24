# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Test ansible module.
"""

import os

import pytest

from antsibull_changelog.ansible import get_ansible_release


def test_ansible_release():
    with pytest.raises(ValueError) as exc:
        get_ansible_release()
    assert str(exc.value) == 'Cannot import ansible.release'

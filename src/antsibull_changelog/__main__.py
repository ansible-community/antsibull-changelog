# coding: utf-8
# Author: Felix Fontein <felix@fontein.de>
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Executable entrypoint to the antsibull_changelog module.

Called by "python -m antsibull_changelog".
"""

import sys

from .cli import run


args = ['{0} -m antsibull_changelog'.format(sys.executable)] + sys.argv[1:]

sys.exit(run(args))

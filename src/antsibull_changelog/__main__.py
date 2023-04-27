# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Executable entrypoint to the antsibull_changelog module.

Called by "python -m antsibull_changelog".
"""

from __future__ import annotations

import sys

from .cli import run

args = ["{0} -m antsibull_changelog".format(sys.executable)] + sys.argv[1:]

sys.exit(run(args))

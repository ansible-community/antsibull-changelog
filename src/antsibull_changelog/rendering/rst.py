# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Functionality for rendering a ReStructuredText document.
"""

from __future__ import annotations

from docutils.utils import column_width as _column_width  # pyre-ignore[21]


def rst_escape(value: str, escape_ending_whitespace=False) -> str:
    """
    Escape RST specific constructs.
    """
    value = value.replace("\\", "\\\\")
    value = value.replace("<", "\\<")
    value = value.replace(">", "\\>")
    value = value.replace("_", "\\_")
    value = value.replace("*", "\\*")
    value = value.replace("`", "\\`")

    if escape_ending_whitespace and value.endswith(" "):
        value = value + "\\ "
    if escape_ending_whitespace and value.startswith(" "):
        value = "\\ " + value

    return value


def column_width(string: str) -> int:
    """
    Return column width of string.

    This is needed for title under- and overlines.
    """
    return _column_width(string)


__ALL__ = ("rst_escape", "column_width")

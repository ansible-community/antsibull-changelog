# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Utility code for rendering.
"""

from __future__ import annotations

from antsibull_docutils.utils import SupportedParser

from ..config import TextFormat


def get_parser_name(text_format: TextFormat) -> SupportedParser:
    """
    Convert a TextFormat to a docutils parser name.
    """
    if text_format == TextFormat.MARKDOWN:
        return "markdown"
    if text_format == TextFormat.RESTRUCTURED_TEXT:
        return "restructuredtext"
    raise ValueError(f"Unsupported format {format}")


__all__ = ("get_parser_name",)

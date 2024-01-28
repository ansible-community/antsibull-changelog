# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Utility code for rendering.
"""

# pyre-ignore-all-errors

from __future__ import annotations

import typing as t
from dataclasses import dataclass

from docutils.core import publish_parts
from docutils.utils import Reporter as DocutilsReporter

from ..fragment import FragmentFormat

SupportedParser = t.Union[t.Literal["restructuredtext"], t.Literal["markdown"]]


_DOCUTILS_PUBLISH_SETTINGS = {
    "input_encoding": "unicode",
    "file_insertion_enabled": False,
    "raw_enabled": False,
    "_disable_config": True,
    "report_level": DocutilsReporter.SEVERE_LEVEL + 1,
}


def get_parser_name(text_format: FragmentFormat) -> SupportedParser:
    """
    Convert a FragmentFormat to a docutils parser name.
    """
    if text_format == FragmentFormat.MARKDOWN:
        return "markdown"
    if text_format == FragmentFormat.RESTRUCTURED_TEXT:
        return "restructuredtext"
    raise ValueError(f"Unsupported format {format}")


@dataclass
class RenderResult:
    """
    A rendering result.
    """

    # The output of the renderer.
    output: str

    # The set of class names found that weren't supported by this renderer.
    unsupported_class_names: set[str]


def get_document_structure(
    source: str, /, parser_name: SupportedParser
) -> RenderResult:
    """
    Render the document as its internal docutils structure.
    """
    parts = publish_parts(
        source=source,
        parser_name=parser_name,
        settings_overrides=_DOCUTILS_PUBLISH_SETTINGS,
    )
    return RenderResult(parts["whole"], set())


def ensure_newline_after_last_content(lines: list[str]) -> None:
    """
    Ensure that if ``lines`` is not empty, the last entry is ``""``.
    """
    if lines and lines[-1] != "":
        lines.append("")


__all__ = (
    "SupportedParser",
    "RenderResult",
    "get_document_structure",
    "ensure_newline_after_last_content",
)

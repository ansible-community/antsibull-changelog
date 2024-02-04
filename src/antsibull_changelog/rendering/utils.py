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

import io
import typing as t
from dataclasses import dataclass

from docutils.core import publish_parts
from docutils.utils import Reporter as DocutilsReporter

from ..config import TextFormat

SupportedParser = t.Union[t.Literal["restructuredtext"], t.Literal["markdown"]]


_DOCUTILS_PUBLISH_SETTINGS = {
    "input_encoding": "unicode",
    "file_insertion_enabled": False,
    "raw_enabled": False,
    "_disable_config": True,
    "report_level": DocutilsReporter.ERROR_LEVEL,
}


def get_docutils_publish_settings(
    warnings_stream: io.IOBase | None = None,
) -> dict[str, t.Any]:
    """
    Provide docutils publish settings.
    """
    settings = _DOCUTILS_PUBLISH_SETTINGS.copy()
    settings["warning_stream"] = warnings_stream or False
    return settings


def get_parser_name(text_format: TextFormat) -> SupportedParser:
    """
    Convert a TextFormat to a docutils parser name.
    """
    if text_format == TextFormat.MARKDOWN:
        return "markdown"
    if text_format == TextFormat.RESTRUCTURED_TEXT:
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

    # List of warnings emitted
    warnings: list[str]


def get_document_structure(
    source: str, /, parser_name: SupportedParser
) -> RenderResult:
    """
    Render the document as its internal docutils structure.
    """
    warnings_stream = io.StringIO()
    parts = publish_parts(
        source=source,
        parser_name=parser_name,
        settings_overrides=get_docutils_publish_settings(warnings_stream),
    )
    return RenderResult(parts["whole"], set(), warnings_stream.getvalue().splitlines())


def ensure_newline_after_last_content(lines: list[str]) -> None:
    """
    Ensure that if ``lines`` is not empty, the last entry is ``""``.
    """
    if lines and lines[-1] != "":
        lines.append("")


__all__ = (
    "SupportedParser",
    "RenderResult",
    "get_docutils_publish_settings",
    "get_document_structure",
    "ensure_newline_after_last_content",
)

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Functionality for rendering a ReStructuredText document.
"""

from __future__ import annotations

from antsibull_docutils.rst_utils import column_width, rst_escape
from antsibull_docutils.utils import ensure_newline_after_last_content

from ..config import TextFormat
from ._document import (
    AbstractRendererEx,
    BaseContent,
    DocumentRendererEx,
    render_document,
    render_section,
)
from .document import SectionRenderer

_SECTION_UNDERLINES = """=-~^.*+:`'"_#"""


class RSTTOCRenderer(BaseContent):
    """
    Render a Table of contents as RST.
    """

    title: str | None
    max_depth: int | None
    level: int

    def __init__(self, title: str | None, max_depth: int | None, level: int):
        super().__init__(already_closed=True)
        self.title = title
        self.max_depth = max_depth
        self.level = level

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        ensure_newline_after_last_content(lines)
        if self.title:
            lines.append(f".. contents:: {rst_escape(self.title)}")
        else:
            lines.append(".. contents::")
        if self.level > 0:
            lines.append("  :local:")
        if self.max_depth is not None:
            lines.append(f"  :depth: {self.max_depth}")
        lines.append("")


class RSTAbstractRenderer(AbstractRendererEx):
    """
    Abstract RST renderer.
    """

    root: "RSTDocumentRenderer"

    def __init__(self, root: "RSTDocumentRenderer"):
        super().__init__(root, "- ")

    def add_section(self, title: str) -> SectionRenderer:
        if self.closed:
            raise ValueError("{self} is already closed")
        section = RSTSectionRenderer(self._get_level() + 1, title, self.root)
        self.content.append(section)
        return section

    def add_toc(self, title: str | None = None, max_depth: int | None = None) -> None:
        if self.closed:
            raise ValueError("{self} is already closed")
        self.content.append(RSTTOCRenderer(title, max_depth, self._get_level()))


class RSTSectionRenderer(RSTAbstractRenderer, SectionRenderer):
    """
    Render a section as RST.
    """

    _level: int

    title: str

    root: "RSTDocumentRenderer"

    def __init__(self, level: int, title: str, root: "RSTDocumentRenderer"):
        super().__init__(root=root)
        self._level = level
        self.title = title

    def _get_level(self) -> int:
        return self._level

    def close(self) -> None:
        self._check_content_closed()
        self.closed = True

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        ensure_newline_after_last_content(lines)
        level = max(0, self._level - 1)
        lines.append(self.title)
        lines.append(self.root.section_underlines[level] * column_width(self.title))
        lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_section(self)


class RSTDocumentRenderer(RSTAbstractRenderer, DocumentRendererEx):
    """
    Render a document as RST.
    """

    unsupported_class_names: set[str]
    raw_preamble: str | None
    document_label: str | None
    section_underlines: str

    def __init__(self, start_level: int = 0, *, section_underlines: str | None = None):
        super().__init__(root=self)
        DocumentRendererEx.__init__(self, start_level=start_level)
        self.unsupported_class_names = set()
        self.raw_preamble = None
        self.document_label = None
        self.section_underlines = section_underlines or _SECTION_UNDERLINES

    def _get_level(self) -> int:
        return self.start_level

    def render_text(self, text: str, text_format: TextFormat) -> str:
        """
        Render a text as ReStructured Text.
        """
        if text_format == TextFormat.RESTRUCTURED_TEXT:
            return text
        raise ValueError(
            f"Text format {text_format} is currently not supported in RST documents!"
        )

    def set_raw_preamble(self, preamble: str) -> None:
        """
        Set a raw preamble to be inserted before the document's title and label.
        """
        if self.raw_preamble is not None:
            raise ValueError("Raw preamble already set")
        self.raw_preamble = preamble

    def set_document_label(self, document_label: str) -> None:
        """
        Set a RST label for the document itself.
        """
        if self.document_label is not None:
            raise ValueError("Document label already set")
        self.document_label = document_label

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        if self.raw_preamble is not None:
            lines.append(self.raw_preamble)
        if self.title is not None:
            title = rst_escape(self.title)
            line = "=" * column_width(title)
            if self.document_label:
                lines.append(f".. _{self.document_label}:")
                lines.append("")
            lines.append(line)
            lines.append(title)
            lines.append(line)
            lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_document(self, self)

    def get_warnings(self) -> list[str]:
        return []


__all__ = ("RSTDocumentRenderer",)

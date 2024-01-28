# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Functionality for rendering a ReStructuredText document.
"""

from __future__ import annotations

from ..fragment import FragmentFormat
from ._document import (
    AbstractRendererEx,
    BaseContent,
    DocumentRendererEx,
    render_document,
)
from .document import SectionRenderer
from .rst import column_width, rst_escape
from .utils import ensure_newline_after_last_content

_SECTION_UNDERLINES = """=-~^.*+:`'"_#"""


class RSTTOCRenderer(BaseContent):
    """
    Render a Table of contents as RST.
    """

    title: str | None
    max_depth: int | None

    def __init__(self, title: str | None, max_depth: int | None):
        super().__init__(already_closed=True)
        self.title = title
        self.max_depth = max_depth

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        if self.title:
            lines.append(f".. contents:: {rst_escape(self.title)}")
        else:
            lines.append(".. contents::")
        if start_level:
            lines.append("  :local:")
        if self.max_depth is not None:
            lines.append("  :depth: {self.max_depth}")
        lines.append("")
        lines.append("")


class RSTAbstractRenderer(AbstractRendererEx):
    """
    Abstract RST renderer.
    """

    def __init__(self, root: DocumentRendererEx):
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
        self.content.append(RSTTOCRenderer(title, max_depth))


class RSTSectionRenderer(RSTAbstractRenderer, SectionRenderer):
    """
    Render a section as RST.
    """

    _level: int

    title: str

    def __init__(self, level: int, title: str, root: DocumentRendererEx):
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
        lines.append(_SECTION_UNDERLINES[level] * column_width(self.title))
        lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        # Check
        if not self.closed:
            raise ValueError(f"Section {self} is not closed")

        # Make sure everything is generated
        self.generate()
        for content in self.content:
            content.generate()

        # Generate lines
        lines: list[str] = []
        self.append_lines(lines)

        # Return lines
        return "\n".join(lines) + "\n"  # add trailing newline


class RSTDocumentRenderer(RSTAbstractRenderer, DocumentRendererEx):
    """
    Render a document as RST.
    """

    unsupported_class_names: set[str]

    def __init__(self, start_level: int = 0):
        super().__init__(root=self)
        DocumentRendererEx.__init__(self, start_level=start_level)
        self.unsupported_class_names = set()

    def _get_level(self) -> int:
        return self.start_level

    def render_text(self, text: str, text_format: FragmentFormat) -> str:
        """
        Render a text as ReStructured Text.
        """
        if text_format == FragmentFormat.RESTRUCTURED_TEXT:
            return text
        raise ValueError(
            f"Text format {text_format} is currently not supported in RST documents!"
        )

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        if self.title is not None:
            title = rst_escape(self.title)
            line = "=" * column_width(title)
            lines.append(line)
            lines.append(title)
            lines.append(line)
            lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_document(self, self)


__all__ = ("RSTDocumentRenderer",)

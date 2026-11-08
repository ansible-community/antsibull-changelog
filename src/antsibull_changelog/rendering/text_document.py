# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Functionality for rendering a text document.
"""

from __future__ import annotations

from antsibull_docutils.text import (
    GlobalContext,
    UseAnsiFormattingType,
    UseUnicodeSplittingType,
)
from antsibull_docutils.text import get_column_count as _get_column_count
from antsibull_docutils.text import render_as_text
from antsibull_docutils.text import render_bold as _render_bold
from antsibull_docutils.text import render_title as _render_title
from antsibull_docutils.utils import ensure_newline_after_last_content

from ..config import TextFormat
from ._document import (
    AbstractRendererEx,
    BaseContent,
    DocumentRendererEx,
    TOCEntry,
    collect_toc_entries,
    render_document,
    render_section,
)
from .document import SectionRenderer
from .utils import get_parser_name


class TextTOCRenderer(BaseContent):
    """
    Render a Table of contents as text.
    """

    owner: "TextAbstractRenderer"
    title: str | None
    max_depth: int | None
    toc: "list[TOCEntry[TextSectionRenderer]] | None"

    def __init__(
        self,
        owner: "TextAbstractRenderer",
        title: str | None,
        max_depth: int | None,
        level: int,
    ):
        super().__init__(already_closed=True)
        self.owner = owner
        self.title = title
        self.max_depth = max_depth
        self.level = level
        self.toc = None

    def generate(self) -> None:
        self.toc = collect_toc_entries(
            content=self.owner.content,
            max_depth=self.max_depth,
            clazz=TextSectionRenderer,
        )

    def _append_toc_entry(self, lines: list[str], entry: TOCEntry, indent: str) -> None:
        lines.append(f"{indent}- {entry.section.title}")
        next_indent = indent + " " * 2
        for child in entry.children:
            self._append_toc_entry(lines, child, next_indent)

    # pylint: disable=duplicate-code
    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        toc = self.toc
        if toc is None:
            raise ValueError("Forgot to call generate()")
        ensure_newline_after_last_content(lines)
        if self.title:
            lines.append(
                # pylint: disable-next=protected-access
                _render_bold(self.title, global_context=self.owner.root._context)
            )
            lines.append("")
        for entry in toc:
            self._append_toc_entry(lines, entry, "")
        ensure_newline_after_last_content(lines)


class TextAbstractRenderer(AbstractRendererEx):  # pylint: disable=abstract-method
    """
    Abstract text renderer.
    """

    root: "TextDocumentRenderer"

    def __init__(self, root: "TextDocumentRenderer"):
        super().__init__(root, "- ")

    def add_section(self, title: str) -> SectionRenderer:
        if self.closed:
            raise ValueError("{self} is already closed")
        section = TextSectionRenderer(self._get_level() + 1, title, self.root)
        self.content.append(section)
        return section

    def add_toc(self, title: str | None = None, max_depth: int | None = None) -> None:
        if self.closed:
            raise ValueError("{self} is already closed")
        self.content.append(TextTOCRenderer(self, title, max_depth, self._get_level()))


class TextSectionRenderer(TextAbstractRenderer, SectionRenderer):
    """
    Render a section as text.
    """

    _level: int

    title: str

    root: "TextDocumentRenderer"

    def __init__(self, level: int, title: str, root: "TextDocumentRenderer"):
        super().__init__(root=root)
        self._level = level
        self.title = title

    # pylint: disable=duplicate-code
    def _get_level(self) -> int:
        return self._level

    def close(self) -> None:
        self._check_content_closed()
        self.closed = True

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        ensure_newline_after_last_content(lines)
        level = max(0, self._level)
        # pylint: disable=protected-access
        lines.extend(
            _render_title(
                self.title, level=level + 1, global_context=self.root._context
            )
        )
        lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_section(self)


class TextDocumentRenderer(TextAbstractRenderer, DocumentRendererEx):
    """
    Render a document as text.
    """

    def __init__(
        self,
        start_level: int = 0,
        *,
        column_width: int = 80,
        use_ansi_formatting: UseAnsiFormattingType = "never",
        use_unicode_splitting: UseUnicodeSplittingType = "always",
    ):
        super().__init__(root=self)
        DocumentRendererEx.__init__(self, start_level=start_level)
        self._column_width = column_width
        self._context = GlobalContext()
        self._context.column_width = column_width
        self._context.use_ansi_formatting = use_ansi_formatting
        self._context.use_unicode_splitting = use_unicode_splitting

    def _get_level(self) -> int:
        return self.start_level

    def render_text(
        self, text: str, text_format: TextFormat, *, indent: str | None = None
    ) -> str:
        """
        Render a text as ReStructured Text.
        """
        self._context.column_width = self._column_width - _get_column_count(
            indent or "", global_context=self._context
        )
        result = render_as_text(
            text,
            parser_name=get_parser_name(text_format),
            global_context=self._context,
        )
        self.unsupported_class_names.update(result.unsupported_class_names)
        self.warnings.extend(result.warnings)
        return result.output

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        if self.title is not None:
            # pylint: disable=protected-access
            lines.extend(
                _render_title(self.title, level=1, global_context=self.root._context)
            )
            lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_document(self, self)


__all__ = ("TextDocumentRenderer",)

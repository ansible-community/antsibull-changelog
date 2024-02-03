# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Functionality for rendering a MarkDown document.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import cast

from ..config import TextFormat
from ._document import (
    AbstractRendererEx,
    BaseContent,
    DocumentRendererEx,
    render_document,
    render_section,
)
from .document import SectionRenderer
from .markdown import GlobalContext, html_escape, md_escape, render_as_markdown
from .utils import ensure_newline_after_last_content, get_parser_name

_SPACE_LIKE = re.compile("[ ._-]")
_DISALLOWED_LETTER = re.compile("[^a-zA-Z0-9-]")


@dataclass
class TOCEntry:
    """
    A TOC entry.
    """

    section: "MDSectionRenderer"

    children: "list[TOCEntry]"


class MDTOCRenderer(BaseContent):
    """
    Render a Table of contents as MarkDown.
    """

    owner: "MDAbstractRenderer"
    title: str | None
    max_depth: int | None
    toc: list[TOCEntry] | None

    def __init__(
        self, owner: "MDAbstractRenderer", title: str | None, max_depth: int | None
    ):
        super().__init__(already_closed=True)
        self.owner = owner
        self.title = title
        self.max_depth = max_depth
        self.toc = None

    def _collect_toc_entries(
        self, content: list[BaseContent], max_depth: int | None
    ) -> list[TOCEntry]:
        result = []
        for c in content:
            if isinstance(c, MDSectionRenderer):
                if max_depth in (0, 1):
                    children = []
                else:
                    children = self._collect_toc_entries(
                        c.content, None if max_depth is None else (max_depth - 1)
                    )
                result.append(TOCEntry(c, children))
        return result

    def generate(self) -> None:
        self.toc = self._collect_toc_entries(
            self.owner.content, max_depth=self.max_depth
        )

    def _append_toc_entry(self, lines: list[str], entry: TOCEntry, indent: str) -> None:
        lines.append(
            f'{indent}- <a href="#{html_escape(entry.section.ref_id)}">'
            f"{md_escape(entry.section.title)}</a>"
        )
        next_indent = f"{indent}  "
        for child in entry.children:
            self._append_toc_entry(lines, child, next_indent)

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        toc = self.toc
        if toc is None:
            raise ValueError("Forgot to call generate()")
        ensure_newline_after_last_content(lines)
        if self.title:
            lines.append(f"**{md_escape(self.title)}**")
        for entry in toc:
            self._append_toc_entry(lines, entry, "")


class MDAbstractRenderer(AbstractRendererEx):
    """
    Abstract MarkDown renderer.
    """

    def __init__(self, root: DocumentRendererEx):
        super().__init__(root, "* ")

    def add_section(self, title: str) -> SectionRenderer:
        if self.closed:
            raise ValueError("{self} is already closed")
        section = MDSectionRenderer(self._get_level() + 1, title, self.root)
        self.content.append(section)
        return section

    def add_toc(self, title: str | None = None, max_depth: int | None = None) -> None:
        if self.closed:
            raise ValueError("{self} is already closed")
        self.content.append(MDTOCRenderer(self, title, max_depth))


class MDSectionRenderer(MDAbstractRenderer, SectionRenderer):
    """
    Render a section as MarkDown.
    """

    _level: int

    title: str
    ref_id: str

    def __init__(self, level: int, title: str, root: DocumentRendererEx):
        super().__init__(root=root)
        self._level = level
        self.title = title
        self.ref_id = cast(MDDocumentRenderer, self.root).get_ref_id(self.title)

    def _get_level(self) -> int:
        return self._level

    def close(self) -> None:
        self._check_content_closed()
        self.closed = True

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        ensure_newline_after_last_content(lines)
        heading = "#" * (1 + self._level - start_level)
        lines.append(f'<a id="{html_escape(self.ref_id)}"></a>')
        lines.append(f"{heading} {md_escape(self.title)}")
        lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_section(self)


def _get_slug(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = _SPACE_LIKE.sub("-", text)
    text = _DISALLOWED_LETTER.sub("", text)
    return text.lower()


class MDDocumentRenderer(MDAbstractRenderer, DocumentRendererEx):
    """
    Render a document as MarkDown.
    """

    global_context: GlobalContext
    unsupported_class_names: set[str]

    def __init__(self, start_level: int = 0):
        super().__init__(root=self)
        DocumentRendererEx.__init__(self, start_level=start_level)
        self.global_context = GlobalContext()
        self.unsupported_class_names = set()

    def _get_level(self) -> int:
        return self.start_level

    def render_text(self, text: str, text_format: TextFormat) -> str:
        """
        Render a text as MarkDown.
        """
        if text_format == TextFormat.MARKDOWN:
            return text
        result = render_as_markdown(
            text,
            parser_name=get_parser_name(text_format),
            global_context=self.global_context,
        )
        self.unsupported_class_names.update(result.unsupported_class_names)
        return result.output

    def get_ref_id(self, title: str) -> str:
        """
        Create a reference ID for a section title.
        """
        return self.global_context.register_new_fragment(_get_slug(title))

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        if self.title is not None:
            lines.append(f"# {md_escape(self.title or '')}")
            lines.append("")
        for content in self.content:
            content.append_lines(lines, start_level=start_level)

    def render(self) -> str:
        return render_document(self, self)

    def get_warnings(self) -> list[str]:
        result = []
        if self.unsupported_class_names:
            classnames = ", ".join(sorted(self.unsupported_class_names))
            result.append(
                "Found unsupported docutils class names that could not be converted"
                f" to MarkDown: {classnames}"
            )
        return result


__all__ = ("MDDocumentRenderer",)

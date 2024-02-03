# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Common code for rendering a document.
"""

from __future__ import annotations

import abc

from ..config import TextFormat
from .document import AbstractRenderer, DocumentRenderer
from .utils import ensure_newline_after_last_content


class BaseContent(abc.ABC):
    """
    Abstract content object.
    """

    closed: bool

    def __init__(self, already_closed=False):
        self.closed = already_closed

    def generate(self) -> None:
        """
        Generate data for this content (if dynamic).
        """

    @abc.abstractmethod
    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        """
        Append the lines for this content.
        """


class DocumentRendererEx(DocumentRenderer):
    """
    Abstract extended document renderer
    """

    start_level: int
    title: str | None

    def __init__(self, start_level: int):
        self.start_level = start_level
        self.title = None

    @abc.abstractmethod
    def render_text(self, text: str, text_format: TextFormat) -> str:
        """
        Render a text as ReStructured Text.
        """

    def set_title(self, title: str) -> None:
        if self.title is not None:
            raise ValueError("Document title already set")
        self.title = title


class ParagraphBreak(BaseContent):
    """
    Paragraph break.
    """

    def __init__(
        self,
    ):
        super().__init__(already_closed=True)

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        ensure_newline_after_last_content(lines)


class TextRenderer(BaseContent):
    """
    Render text.
    """

    text: str
    text_format: TextFormat
    root: DocumentRendererEx
    indent_first: str
    indent_next: str

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        text: str,
        text_format: TextFormat,
        /,
        root: DocumentRendererEx,
        indent_first: str = "",
        indent_next: str = "",
    ):
        super().__init__(already_closed=True)
        self.text = text
        self.text_format = text_format
        self.root = root
        self.indent_first = indent_first
        self.indent_next = indent_next

    def append_lines(self, lines: list[str], start_level: int = 0) -> None:
        text = self.root.render_text(self.text, self.text_format)
        indent = self.indent_first
        for line in text.splitlines():
            if not line and indent != self.indent_first:
                lines.append("")
            else:
                lines.append(f"{indent}{line}")
            indent = self.indent_next


class AbstractRendererEx(BaseContent, AbstractRenderer):
    """
    Abstract RST renderer.
    """

    content: list[BaseContent]
    root: DocumentRendererEx
    _fragment_ident: str

    def __init__(self, root: DocumentRendererEx, fragment_ident: str):
        super().__init__()
        self.content = []
        self.root = root
        self._fragment_ident = fragment_ident

    def _check_content_closed(self) -> None:
        for content in self.content:
            if not content.closed:
                raise ValueError(f"Content {content} is not closed")

    @abc.abstractmethod
    def _get_level(self) -> int:
        pass

    def generate(self) -> None:
        for content in self.content:
            content.generate()

    def add_text(self, text: str, text_format: TextFormat) -> None:
        if self.closed:
            raise ValueError("{self} is already closed")
        self.content.append(TextRenderer(text, text_format, root=self.root))

    def add_fragment(self, text: str, text_format: TextFormat) -> None:
        if self.closed:
            raise ValueError("{self} is already closed")
        self.content.append(
            TextRenderer(
                text,
                text_format,
                root=self.root,
                indent_first=self._fragment_ident,
                indent_next="  ",
            )
        )

    def ensure_paragraph_break(self) -> None:
        self.content.append(ParagraphBreak())


def _render(abstract_renderer: AbstractRendererEx, start_level: int = 0) -> str:
    # Make sure everything is generated
    abstract_renderer.generate()
    for content in abstract_renderer.content:
        content.generate()

    # Generate lines
    lines: list[str] = []
    abstract_renderer.append_lines(lines, start_level=start_level)

    # Return lines
    return "\n".join(lines) + "\n"  # add trailing newline


def render_section(
    abstract_renderer: AbstractRendererEx,
) -> str:
    """
    Renders the section to a string.

    :arg abstract_renderer: View of the section as an extended abstract renderer.
    """
    # Check
    if not abstract_renderer.closed:
        raise ValueError(f"Section {abstract_renderer} is not closed")

    return _render(abstract_renderer)


def render_document(
    document_renderer: DocumentRendererEx,
    abstract_renderer: AbstractRendererEx,
) -> str:
    """
    Renders the document to a string.

    :arg document_renderer: View of the document as an extended document renderer.
    :arg abstract_renderer: View of the document as an extended abstract renderer.
    """
    # Check
    abstract_renderer._check_content_closed()  # pylint: disable=protected-access
    if document_renderer.start_level == 0 and document_renderer.title is None:
        raise ValueError("Title must be specified if start_level == 0")

    return _render(
        abstract_renderer,
        start_level=document_renderer.start_level,
    )


__all__ = (
    "BaseContent",
    "DocumentRendererEx",
    "TextRenderer",
    "AbstractRendererEx",
    "render_section",
    "render_document",
)

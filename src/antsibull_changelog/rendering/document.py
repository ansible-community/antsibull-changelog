# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2024, Ansible Project

"""
Abstract functionality for rendering a document.
"""

from __future__ import annotations

import abc

from ..config import TextFormat


class AbstractRenderer(abc.ABC):
    """
    Abstract renderer. Can be a document or section, for example.
    """

    @abc.abstractmethod
    def add_section(self, title: str) -> "SectionRenderer":
        """
        Add a (sub-)section.
        """

    @abc.abstractmethod
    def add_toc(self, title: str | None = None, max_depth: int | None = None) -> None:
        """
        Add a table of contents starting at this section.
        """

    @abc.abstractmethod
    def add_text(self, text: str, text_format: TextFormat) -> None:
        """
        Add a text.
        """

    @abc.abstractmethod
    def add_fragment(self, text: str, text_format: TextFormat) -> None:
        """
        Add a fragment (as a list item).
        """


class SectionRenderer(AbstractRenderer):
    """
    Renders a section.
    """

    def close(self) -> None:
        """
        Closes the section.

        All subsections must be closed before calling this.
        After calling this, no other method but ``render()`` can be called.
        """

    @abc.abstractmethod
    def render(self) -> str:
        """
        Render the document to a string.

        Must be closed before calling this.
        """


class DocumentRenderer(AbstractRenderer):
    """
    Renders a document.
    """

    @abc.abstractmethod
    def set_title(self, title: str) -> None:
        """
        Set the top-level title of the document
        """

    @abc.abstractmethod
    def render(self) -> str:
        """
        Render the document to a string.

        All sections must be closed before calling this.
        """

    @abc.abstractmethod
    def get_warnings(self) -> list[str]:
        """
        Retrieve a list of warnings encountered while rendering.

        Must only be called after calling ``render()``.
        """


__all__ = ("AbstractRenderer", "SectionRenderer", "DocumentRenderer")

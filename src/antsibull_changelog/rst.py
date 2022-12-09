# Author: Matt Clay <matt@mystile.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
ReStructuredText helpers.
"""

from typing import List


class RstBuilder:
    """
    Simple reStructuredText (RST) builder.
    """
    lines: List[str]
    section_underlines: str

    def __init__(self):
        """
        Create RST builder.
        """
        self.lines = []
        self.section_underlines = '''=-~^.*+:`'"_#'''

    def set_title(self, title: str) -> None:
        """
        Add a document title. Must be called before other functions.

        :arg title: The document title
        """
        self.lines.append(self.section_underlines[0] * len(title))
        self.lines.append(title)
        self.lines.append(self.section_underlines[0] * len(title))
        self.lines.append('')

    def add_section(self, name: str, depth: int = 0) -> None:
        """
        Add a section.

        :arg name: The section title
        :arg depth: The section depth
        """
        self.lines.append(name)
        self.lines.append(self.section_underlines[depth] * len(name))
        self.lines.append('')

    def add_raw_rst(self, content: str) -> None:
        """
        Add a raw RST line.
        """
        self.lines.append(content)

    def add_list_item(self, content: str) -> None:
        """
        Add a list item. Content can be multi-lined.
        """
        lines = content.splitlines()
        for line_no, line in enumerate(lines):
            if line_no > 0 and not line:
                self.lines.append('')
                continue
            self.lines.append('%s %s' % (' ' if line_no else '-', line))

    def generate(self) -> str:
        """
        Generate RST content.
        """
        return '\n'.join(self.lines)

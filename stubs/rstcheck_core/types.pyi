# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

import enum
import pathlib

from typing import Literal, Union

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class LintError(TypedDict):
    source_origin: Union[pathlib.Path, Literal["<string>"], Literal["<stdin>"]]
    line_number: int
    message: str

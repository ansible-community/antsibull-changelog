# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
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

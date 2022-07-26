# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

import enum

from typing import List, Optional, Tuple, Union


class ReportLevel(enum.Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3
    SEVERE = 4
    NONE = 5


class RstcheckConfig:
    def __init__(self, report_level: Optional[ReportLevel] = ...): ...

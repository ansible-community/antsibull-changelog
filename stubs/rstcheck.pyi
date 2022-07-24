# -*- coding: utf-8 -*-
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

import docutils.utils

from typing import List, Optional, Tuple, Union


def check(source: str,
          filename: Optional[str] = ...,
          report_level: Union[docutils.utils.Reporter, int] = ...,
          ignore: Union[dict, None] = ...,
          debug: bool = ...) -> List[Tuple[int, str]]: ...

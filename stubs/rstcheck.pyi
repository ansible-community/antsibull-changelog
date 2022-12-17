# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

import docutils.utils

def check(source: str,
          filename: str | None = ...,
          report_level: docutils.utils.Reporter | int = ...,
          ignore: dict | None = ...,
          debug: bool = ...) -> list[tuple[int, str]]: ...

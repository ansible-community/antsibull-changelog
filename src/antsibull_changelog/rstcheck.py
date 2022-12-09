# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2022, Ansible Project

"""
Handle rstcheck.
"""

import os.path
import pathlib
import tempfile
import typing as t

# rstcheck >= 6.0.0 depends on rstcheck-core
try:
    import rstcheck_core.checker
    import rstcheck_core.config
    HAS_RSTCHECK_CORE = True
except ImportError:
    HAS_RSTCHECK_CORE = False
    import docutils.utils
    import rstcheck


def check_rst_content(content: str, filename: t.Optional[str] = None
                      ) -> t.List[t.Tuple[int, int, str]]:
    '''
    Check the content with rstcheck. Return list of errors and warnings.

    The entries in the return list are tuples with line number, column number, and
    error/warning message.
    '''
    if HAS_RSTCHECK_CORE:
        filename = os.path.basename(filename or 'file.rst') or 'file.rst'
        with tempfile.TemporaryDirectory() as tempdir:
            rst_path = os.path.join(tempdir, filename)
            with open(rst_path, 'w', encoding='utf-8') as f:
                f.write(content)
            config = rstcheck_core.config.RstcheckConfig(
                report_level=rstcheck_core.config.ReportLevel.WARNING,
            )
            core_results = rstcheck_core.checker.check_file(pathlib.Path(rst_path), config)
            return [(result['line_number'], 0, result['message']) for result in core_results]
    else:
        results = rstcheck.check(  # pylint: disable=no-member,used-before-assignment
            content,
            filename=filename,
            # pylint: disable-next=used-before-assignment
            report_level=docutils.utils.Reporter.WARNING_LEVEL,
        )
        return [(result[0], 0, result[1]) for result in results]

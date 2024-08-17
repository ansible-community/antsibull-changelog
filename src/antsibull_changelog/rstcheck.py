# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2022, Ansible Project

"""
Handle rstcheck.
"""

from __future__ import annotations

import os.path
import pathlib
import tempfile


def check_rst_content(
    content: str, filename: str | None = None
) -> list[tuple[int, int, str]]:
    """
    Check the content with rstcheck. Return list of errors and warnings.

    The entries in the return list are tuples with line number, column number, and
    error/warning message.
    """
    # rstcheck >= 6.0.0 depends on rstcheck-core
    try:
        # We import from rstcheck_core locally since importing it is rather slow
        import rstcheck_core.checker  # pylint: disable=import-outside-toplevel
        import rstcheck_core.config  # pylint: disable=import-outside-toplevel

        filename = os.path.basename(filename or "file.rst") or "file.rst"
        with tempfile.TemporaryDirectory() as tempdir:
            rst_path = os.path.join(tempdir, filename)
            with open(rst_path, "w", encoding="utf-8") as f:
                f.write(content)
            config = rstcheck_core.config.RstcheckConfig(
                report_level=rstcheck_core.config.ReportLevel.WARNING,
            )
            core_results = rstcheck_core.checker.check_file(
                pathlib.Path(rst_path), config
            )
            return [
                (result["line_number"], 0, result["message"]) for result in core_results
            ]
    except ImportError:
        # We import from rstcheck_core locally since importing it is rather slow
        import docutils.utils  # pylint: disable=import-outside-toplevel
        import rstcheck  # pylint: disable=import-outside-toplevel

        results = rstcheck.check(  # pylint: disable=no-member
            content,
            filename=filename,
            report_level=docutils.utils.Reporter.WARNING_LEVEL,
        )
        return [(result[0], 0, result[1]) for result in results]

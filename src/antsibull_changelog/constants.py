# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project
"""
Constants used by antsibull-changelog.
"""


# Return codes used in cli.py and test files.
RC_SUCCESS = 0  # Success
RC_UNHANDLED_ERROR = 1  # Unhandled error.  See the Traceback for more information.
RC_BAD_CLI_ARG = 2  # There was a problem with the command line arguments.
RC_INVALID_FRAGMENT = 3  # Found invalid changelog fragments.
RC_COMMAND_FAILED = 5  # Problem occurred which prevented the execution of the command.

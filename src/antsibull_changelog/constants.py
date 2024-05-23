# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project


"""
Return codes used in cli.py and test files.
"""

SUCCESS = 0  # Success
UNHANDLED_ERROR = 1  # Unhandled error.  See the Traceback for more information.
BAD_CLI_ARG = 2  # There was a problem with the command line arguments.
INVALID_FRAGMENT = 3  # Found invalid changelog fragments.
OLD_PYTHON = 4  # Needs to be run on a newer version of Python.
COMMAND_FAILED = 5  # Problem occurred which prevented the execution of the command.

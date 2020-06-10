# coding: utf-8
# Author: Felix Fontein <felix@fontein.de>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Executable entrypoint to the antsibull_changelog module.

Called by "python -m antsibull_changelog".
"""

import sys

from .cli import run


args = ['python -m antsibull_changelog'] + sys.argv[1:]

sys.exit(run(args))

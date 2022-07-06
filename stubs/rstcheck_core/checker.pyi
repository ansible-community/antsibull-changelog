import enum
import pathlib

from typing import List, Optional, Tuple, Union

from . import config, types


def check_file(
    source_file: pathlib.Path,
    rstcheck_config: config.RstcheckConfig,
    overwrite_with_file_config: bool = True,
) -> List[types.LintError]: ...

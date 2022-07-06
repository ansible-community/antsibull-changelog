import enum
import pathlib

from typing import Literal, Union


class LintError:
    source_origin: Union[pathlib.Path, Literal["<string>"], Literal["<stdin>"]]
    line_number: int
    message: str

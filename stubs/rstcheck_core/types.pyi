import enum
import pathlib

from typing import Literal, Union

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class LintError(TypedDict):
    source_origin: Union[pathlib.Path, Literal["<string>"], Literal["<stdin>"]]
    line_number: int
    message: str

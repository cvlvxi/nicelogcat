from dataclasses import dataclass
from typing import Union


@dataclass
class Fg:
    black = "\u001b[30m"
    red = "\u001b[31m"
    green = "\u001b[32m"
    yellow = "\u001b[33m"
    blue = "\u001b[34m"
    magenta = "\u001b[35m"
    cyan = "\u001b[36m"
    white = "\u001b[37m"
    default = "\u001b[39m"


@dataclass
class Bg:
    black = "\u001b[40m"
    red = "\u001b[41m"
    green = "\u001b[42m"
    yellow = "\u001b[43m"
    blue = "\u001b[44m"
    magenta = "\u001b[45m"
    cyan = "\u001b[46m"
    white = "\u001b[47m"
    default = "\u001b[49m"


REVERSE = "\u001b[7m"
RESET_REVERSE = "\u001b[27m"
RESET = "\u001b[0m"
ALL_COLORS = [
    x
    for x in Fg.__dict__.values()
    if isinstance(x, str) and not x.startswith("_") and not "()" in x
] + [
    x
    for x in Bg.__dict__.values()
    if isinstance(x, str) and not x.startswith("_") and not "()" in x
]


def style(msg: str, col: Union[Fg, Bg]) -> str:
    return col + msg + RESET


def stylekv(k: str, kcol: Union[Fg, Bg], v: str, vcol: Union[Fg, Bg]) -> str:
    return kcol + k + RESET + ": " + vcol + v + RESET


def remove_col_from_val(val):
    new_val = val
    for col in ALL_COLORS:
        if col in val:
            new_val = new_val.replace(col, "")
    new_val = new_val.replace("\x1b[0m", "")
    return new_val

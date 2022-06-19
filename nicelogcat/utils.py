import json
import random
from dataclasses import is_dataclass
from functools import reduce
from typing import List, TypeVar, Tuple
from colorama import Fore, Style, Back


COLOR_STRS = [
    "BLACK",
    "BLUE",
    "CYAN",
    "GREEN",
    "MAGENTA",
    "RED",
    "WHITE",
    "YELLOW",
]

FORE_COLORS = [
    Fore.YELLOW,
    Fore.WHITE,
    Fore.BLUE,
    Fore.CYAN,
    Fore.GREEN,
    Fore.MAGENTA,
    Fore.RED,
    Fore.LIGHTBLUE_EX,
    Fore.LIGHTCYAN_EX,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTMAGENTA_EX,
    Fore.LIGHTRED_EX,
    Fore.LIGHTWHITE_EX,
    Fore.LIGHTYELLOW_EX,
    Fore.BLACK,
    Fore.LIGHTBLACK_EX,
]

BACK_COLORS = [
    Back.YELLOW,
    Back.WHITE,
    Back.BLUE,
    Back.CYAN,
    Back.GREEN,
    Back.MAGENTA,
    Back.RED,
    Back.LIGHTBLUE_EX,
    Back.LIGHTCYAN_EX,
    Back.LIGHTGREEN_EX,
    Back.LIGHTMAGENTA_EX,
    Back.LIGHTRED_EX,
    Back.LIGHTWHITE_EX,
    Back.LIGHTYELLOW_EX,
    Back.BLACK,
    Back.LIGHTBLACK_EX,
]

COLOR_RESETTERS = [Fore.RESET, Back.RESET, Style.RESET_ALL]

ALL_COLORS = FORE_COLORS + BACK_COLORS + COLOR_RESETTERS

T = TypeVar('T')


def flatten_list(somelist: List[T]) -> List[T]:
    unique = set([
        x for x in reduce(lambda x, y: x + y, somelist)  # type: ignore
        if x
    ])

    return list(unique)


def norm_str(some_str):
    some_str = some_str.strip()
    some_str = some_str.replace('"', "")
    some_str = some_str.replace("'", "")
    some_str = some_str.replace("\\", "")
    return some_str


def norm_str2(some_str):
    some_str = some_str.replace("\\n", "\n")
    some_str = some_str.replace("\\", "")
    some_str = some_str.replace('""', '"')
    some_str = some_str.replace("''", "'")
    some_str = some_str.replace('":"', '": "')
    return some_str


def norm_str3(some_str):
    some_str = some_str.strip()
    if not some_str:
        return ""
    bad_chars = ":\\/\\'\""
    if some_str[0] in bad_chars:
        some_str = some_str[1:]
    if len(some_str) > 1 and some_str[-1] in bad_chars:
        some_str = some_str[0:-1]
    return some_str


LOG_LEVEL_CHOICES = {
    "e": "ERROR",
    "error": "ERROR",
    "ERROR": "ERROR",
    "w": "WARN",
    "warn": "WARN",
    "WARN": "WARN",
    "d": "DEBUG",
    "debug": "DEBUG",
    "DEBUG": "DEBUG",
    "i": "INFO",
    "info": "INFO",
    "INFO": "INFO",
    "v": "VERBOSE",
    "verbose": "VERBOSE",
    "VERBOSE": "VERBOSE",
    "f": "FATAL",
    "fatal": "FATAL",
    "FATAL": "FATAL",
    "s": "SILENT",
    "silent": "SILENT",
    "SILENT": "SILENT",
}


def find_index_in_most_common(most_common: List[Tuple[str, int]],
                              line: str) -> int:
    print(most_common)
    print(line)
    key_list = [x[0] for x in most_common]
    idx = key_list.index(line)
    return idx


def uplift_flat_dict(d: dict) -> dict:
    d2 = {}
    for k, v in d.items():
        if isinstance(v, dict):
            d2[k] = uplift_flat_dict(v)
        if '.' in k:
            k_parts = k.split('.', 1)
            uplift_k = k_parts[0]
            other_k = k_parts[1]
            if uplift_k not in d2:
                d2[uplift_k] = {}
            d2[uplift_k][other_k] = v
        else:
            d2[k] = v
    return d2


def r_merge_dicts(d1: dict, d2: dict, smaller_r: bool = False) -> dict:
    d3 = {}
    for key in d1.keys():
        if not smaller_r:
            assert key in d2.keys()
    for key1, value1 in d1.items():
        if not smaller_r:
            assert key1 in d2
        else:
            if key1 not in d2:
                d3[key1] = value1
                continue
        value2 = d2[key1]
        if value1 == None  and value2 != None:
            value1 = value2
        elif value2 == None and value1 != None:
            value2 = value1
        assert type(value1) == type(value2)
        if isinstance(value1, dict):
            d3[key1] = r_merge_dicts(value1, value2, smaller_r=smaller_r)
        elif isinstance(value1, list):
            new_list = value1
            for v in value2:
                if v not in new_list:
                    new_list.append(v)
            d3[key1] = new_list
        else:
            d3[key1] = value2
    return d3


LOG_VALS = set(LOG_LEVEL_CHOICES.values())
# MAX_LOG_WIDTH = max([len(x) for x in LOG_VALS])
MAX_LOG_WIDTH = 5


def remove_col_from_val(val):
    new_val = val
    for col in ALL_COLORS:
        if col in val:
            new_val = new_val.replace(col, "")
    return new_val


def style(val: str, color=None):
    if not val or not isinstance(val, str):
        return val
    if isinstance(color, tuple):
        color = color[0]
    new_val = remove_col_from_val(val)
    if color:
        val = color + new_val + Style.RESET_ALL
    return val

def pstyle(msg: str, color) -> str:
    return print(style(msg, color))


def nested_dicts(some_dict: dict, level: int = 0):
    new_dict = {}
    for k, v in some_dict.items():
        value = None
        try:
            value = json.loads(v)
        except Exception:
            value = v
        if not isinstance(value, dict):
            new_dict[k] = v
            continue
        for subk, subv in value.items():
            if isinstance(subv, dict):
                new_dict[subk] = nested_dicts(subv, level=level + 1)
            else:
                if subk in new_dict.keys():
                    continue
                    # subk = f"{subk}_{level}"
                new_dict[subk] = subv
    return new_dict


def find_dict_in_v(v, rawline=None):
    if not isinstance(v, str):
        if isinstance(v, dict):
            return v
        else:
            return {}
    else:
        if "{" in v and "}" in v:
            first_bracket_idx = v.find("{")
            last_bracket_idx = v.rfind("}")
            v = v.replace("'", '"')
            json_str = v[first_bracket_idx:last_bracket_idx + 1]
            try:
                val = json.loads(json_str)
                return val
            except Exception:
                return {}
    return {}


def flatten_dict(d):
    new_dict = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict):
                new_dict.update(flatten_dict(v))
            else:
                new_dict[k] = v
    return new_dict


def rand_prefix_colors(stack_trace_colors: dict,
                       prefix: str,
                       ignore_col: any = None) -> dict:
    ignore_index = None
    if ignore_col:
        try:
            ignore_index = BACK_COLORS.index(ignore_col)
        except Exception:
            try:
                ignore_index = FORE_COLORS.index(ignore_col)
            except Exception:
                pass
    rand_idx = None
    if ignore_index:
        while True:
            rand_idx = random.randint(2, 11)
            if rand_idx != ignore_index:
                break
    else:
        rand_idx = random.randint(2, 11)
    back_col = BACK_COLORS[rand_idx]
    fore_col = FORE_COLORS[rand_idx]

    if prefix not in stack_trace_colors:
        stack_trace_colors[prefix] = (back_col, fore_col)
    return stack_trace_colors


def explode_single_item_list(some_list):
    item = []
    if len(some_list) == 1:
        item = some_list[0]
        quoted = item.count('"') >= 1
        space_delimited = item.count(' ') >= 1
        if space_delimited:
            item = item.replace('[', '').replace(']', '').strip()
            if quoted:
                item = item.split('\" ')
                item = [x.replace('"', '') for x in item if x]
            else:
                item = item.split(' ')
    if isinstance(item, str):
        item = [item]
    return item

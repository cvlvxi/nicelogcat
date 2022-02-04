import re
import json
import random
from datetime import datetime
from functools import reduce
from typing import List, TypeVar
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


def merge_dicts(d1: dict, d2: dict, choose_right: bool = True) -> dict:
    d3 = {}
    for key in d1.keys():
        assert key in d2.keys()
    for key1, value1 in d1.items():
        assert key1 in d2
        value2 = d2[key1]
        assert type(value1) == type(value2)
        if isinstance(value1, dict):
            d3[key1] = merge_dicts(value1, value2)
        if isinstance(value1, list):
            d3[key1] = value1 + value2
        else:
            d3[key1] = value2
    return d3


LOG_VALS = set(LOG_LEVEL_CHOICES.values())
# MAX_LOG_WIDTH = max([len(x) for x in LOG_VALS])
MAX_LOG_WIDTH = 5


def get_log_level(log_level, colors):
    result = [None, None, MAX_LOG_WIDTH]
    if log_level.lower() == "w":
        result[0] = colors["LEVEL_WARN_COLOR"]
        result[1] = "WARN"
    elif log_level.lower() == "e":
        result[0] = colors["LEVEL_ERROR_COLOR"]
        result[1] = "ERROR"
    elif log_level.lower() == "d":
        result[0] = colors["LEVEL_WARN_COLOR"]
        result[1] = "DEBUG"
    elif log_level.lower() == "i":
        result[0] = colors["LEVEL_INFO_COLOR"]
        result[1] = "INFO"
    elif log_level.lower() == "v":
        result[0] = colors["LEVEL_INFO_COLOR"]
        result[1] = "VERBOSE"
    elif log_level.lower() == "f":
        result[0] = colors["LEVEL_ERROR_COLOR"]
        result[1] = "FATAL"
    elif log_level.lower() == "s":
        result[0] = Fore.BLACK
        result[1] = "SILENT"
    else:
        raise ValueError("Unknown log_level found: {}".format(log_level))
    return result


def remove_col_from_val(val):
    new_val = val
    for col in ALL_COLORS:
        if col in val:
            new_val = new_val.replace(col, "")
    return new_val


def style(val: str, color=None):
    if not val or not isinstance(val, str):
        return val
    new_val = remove_col_from_val(val)
    if color:
        val = color + new_val + Style.RESET_ALL
    return val


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


def nice_print_dict(key_count, top_spacer, some_dict, key_color, value_color,
                    args):
    nice_str = ""
    nice_strings = []

    for k, v in some_dict.items():
        if isinstance(v, dict):
            (new_key_count,
             nice_str) = nice_print_dict(key_count, top_spacer, v, key_color,
                                         value_color, args)

            nice_strings.append(nice_str)
            key_count = new_key_count
        else:
            if args.IGNORE_KEYS:
                if k in args.IGNORE_KEYS:
                    continue
            spacer = ""
            if args.PER_LINE != -1:
                if key_count % args.PER_LINE == 0:
                    spacer = top_spacer
                else:
                    spacer = ""
            nice_strings.append(spacer + args.SPACER + "{}{}: {}{}".format(
                args.LEFT_OF_KEY_VALUE,
                style(str(k).strip(), color=key_color),
                style(str(v).strip(), color=value_color),
                args.RIGHT_OF_KEY_VALUE,
            ))
            key_count += 1
    if nice_strings:
        nice_str = args.SPACER.join([x for x in nice_strings if x])
    return (key_count, nice_str)


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
                       ignore_col: any = None):
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


def find_stack(
    stack_trace_map: dict,
    pfix: str,
    string_dict: dict,
    stack_trace_colors: dict,
    log_time: str,
    args: dict,
    is_recording: bool,
):
    if not pfix or (args.PREFIXES and pfix not in args.PREFIXES):
        return ""
    if pfix not in stack_trace_map:
        stack_trace_map[pfix] = {
            "prefixes": [],
            "stacktraces": [],
            "started": False
        }
        rand_prefix_colors(stack_trace_colors, pfix)
    if "stack" in string_dict:
        stack_msg = string_dict["stack"]
        stack_parts = stack_msg.split("\n", 1)
        stack_prefixes = stack_parts[0]
        stacktraces = stack_parts[1].split("\n")
        return assemble_stack_str(
            log_time=log_time,
            prefix=pfix,
            stack_trace_prefixes=[stack_prefixes],
            stack_trace_lines=stacktraces,
            stack_trace_colors=stack_trace_colors,
            args=args,
            is_recording=is_recording,
        )
    stack_trace_str = ""
    if "message" not in string_dict:
        return ""
    message = string_dict["message"]
    message = message.strip()
    is_a_stack_trace = message.startswith("at ")
    stack_prefixes = stack_trace_map[pfix]["prefixes"]
    stacktraces = stack_trace_map[pfix]["stacktraces"]
    started = stack_trace_map[pfix]["started"]
    if is_a_stack_trace:
        if not started:
            stack_trace_map[pfix]["started"] = True
        stacktraces.append(message)
    else:
        stack_prefixes.append(message)
        if stack_trace_map[pfix]["started"] and len(stacktraces) > 0:
            stack_trace_str = clear_stack(
                stack_trace_map,
                pfix,
                stack_trace_colors,
                log_time,
                args=args,
                is_recording=is_recording,
            )
    if len(stack_prefixes) == args.PREV_MSGS_BEFORE_STACK_TRACE:
        stack_trace_map[pfix]["prefixes"] = []
    return stack_trace_str


def assemble_stack_str(
    log_time: str,
    prefix: str,
    stack_trace_prefixes: List[str],
    stack_trace_lines: List[str],
    stack_trace_colors: dict,
    args: dict,
    is_recording: bool,
):

    if args.linespace > 0:
        stack_trace_str = "\n" * args.linespace
    else:
        stack_trace_str = ""

    stack_trace_str += style("-" * 80, color=Fore.BLACK + Back.BLACK)
    stack_trace_str += "\n"
    if args.ALLOW_RECORD and is_recording:
        stack_trace_str += "🟢 "
    if args.ALLOW_RECORD and not is_recording:
        stack_trace_str += "🔴 "

    # Header Line
    back_color, fore_color = stack_trace_colors[prefix]
    # stack_trace_str += style(f"{prefix}Exception", fore_color)
    stack_trace_str += style(f" {prefix}", fore_color)
    # stack_trace_str += style(" @ ", back_color + Fore.BLACK)
    # stack_trace_str += style(" " * 5, back_color + Fore.BLACK)
    # stack_trace_str += style(f"Current Time: {datetime.now().ctime()}", Back.GREEN + Fore.BLACK)
    # stack_trace_str += style(" " * 5, back_color + Fore.BLACK)
    # stack_trace_str += "\n"
    # Stack Prefixes

    if not args.flat:
        stack_trace_str += "\n"
    stack_trace_str += style("\n".join([x for x in stack_trace_prefixes if x]),
                             color=Fore.YELLOW)

    biggest_index = len(stack_trace_lines) - 1
    num_stack_traces = min(args.NUM_STACK_TRACES_TO_PRINT, biggest_index)
    continued_str = ""
    if num_stack_traces < biggest_index:
        continued_str = "\n\n(...continued)"

    file_regex = r".*\((.*)\).*"
    tab_space = " " * 4
    for stack_trace in stack_trace_lines[:num_stack_traces]:
        result = re.match(file_regex, stack_trace)
        print_default = False
        if result:
            file_path_str = result.group(1)
            if ":" not in file_path_str:
                print_default = True
            else:
                parts = file_path_str.split(":", 1)
                before_path = stack_trace.split(file_path_str)[0]
                file_path = parts[0]
                line_num = parts[1]
                new_stack_trace = ""
                new_stack_trace += before_path
                new_stack_trace += style(file_path, color=Fore.CYAN) + ":"
                new_stack_trace += style(line_num, color=Fore.YELLOW)
                stack_trace_str += f"\n{tab_space}{new_stack_trace}"
                print_default = False

        else:
            print_default = True
        if print_default:
            stack_trace_str += f"\n{tab_space}{stack_trace}"

    # stack_trace_str += "\n\t".join(stack_trace_lines[:num_stack_traces])
    # stack_trace_str += "\n"
    stack_trace_str += continued_str

    return stack_trace_str


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


def clear_stack(
    stack_trace_map: dict,
    pfix: str,
    stack_trace_colors: dict,
    log_time: str,
    args: dict,
    is_recording: bool,
):
    stack_trace_str = assemble_stack_str(
        log_time=log_time,
        prefix=pfix,
        stack_trace_prefixes=stack_trace_map[pfix]["prefixes"],
        stack_trace_lines=stack_trace_map[pfix]["stacktraces"],
        stack_trace_colors=stack_trace_colors,
        args=args,
        is_recording=is_recording,
    )
    stack_trace_map[pfix]["started"] = False
    stack_trace_map[pfix]["prefixes"] = []
    stack_trace_map[pfix]["stacktraces"] = []
    return stack_trace_str

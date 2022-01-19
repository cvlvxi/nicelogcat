
import json
import random
from functools import reduce
from colorama import Fore, Style, Back
from typing import List

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
}

COLOR_RESETTERS = [Fore.RESET, Back.RESET, Style.RESET_ALL]

ALL_COLORS = FORE_COLORS + BACK_COLORS + COLOR_RESETTERS


def flatten_list(somelist: list):
    unique = set([x for x in reduce(lambda x, y: x + y, somelist) if x])

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


def get_log_level(log_level, colors):
    if log_level.lower() == "w":
        return colors["LEVEL_WARN_COLOR"] + "WARN" + Style.RESET_ALL
    elif log_level.lower() == "e":
        return colors["LEVEL_ERROR_COLOR"] + "ERROR" + Style.RESET_ALL
    elif log_level.lower() == "d":
        return colors["LEVEL_WARN_COLOR"] + "DEBUG" + Style.RESET_ALL
    elif log_level.lower() == "i":
        return colors["LEVEL_INFO_COLOR"] + "INFO" + Style.RESET_ALL
    elif log_level.lower() == "v":
        return colors["LEVEL_INFO_COLOR"] + "VERBOSE" + Style.RESET_ALL
    elif log_level.lower() == "f":
        return colors["LEVEL_ERROR_COLOR"] + "FATAL" + Style.RESET_ALL
    elif log_level.lower() == "s":
        return Fore.BLACK + "SILENT" + Style.RESET_ALL
    else:
        raise ValueError("Unknown log_level found: {}".format(log_level))


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


def nice_print_dict(
    key_count, top_spacer, some_dict, key_color, value_color, args
):
    nice_str = ""
    nice_strings = []

    for k, v in some_dict.items():
        if isinstance(v, dict):
            (new_key_count, nice_str) = nice_print_dict(
                key_count, top_spacer, v, key_color, value_color, args
            )

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
            nice_strings.append(
                spacer
                + args.SPACER
                + "{}{}: {}{}".format(
                    args.LEFT_OF_KEY_VALUE,
                    style(str(k).strip(), color=key_color),
                    style(str(v).strip(), color=value_color),
                    args.RIGHT_OF_KEY_VALUE,
                )
            )
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
            json_str = v[first_bracket_idx: last_bracket_idx + 1]
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


def find_stack(
    stack_trace_map: dict,
    pfix: str,
    string_dict: dict,
    stack_trace_colors: dict,
    log_time: str,
    args: dict
):
    if not pfix or (args.PREFIXES and pfix not in args.PREFIXES):
        return ""
    if pfix not in stack_trace_map:
        stack_trace_map[pfix] = {
            "prefixes": [],
            "stacktraces": [],
            "started": False
            # "flushed": False
        }
        rand_idx = random.randint(2, 11)
        stack_trace_colors[pfix] = (
            BACK_COLORS[rand_idx],
            FORE_COLORS[rand_idx]
        )
    if "stack" in string_dict:
        stack_msg = string_dict["stack"]
        stack_parts = stack_msg.split("\n", 1)
        stack_prefixes = stack_parts[0]
        stacktraces = stack_parts[1].split('\n')
        return assemble_stack_str(
            log_time=log_time,
            prefix=pfix,
            stack_trace_prefixes=[stack_prefixes],
            stack_trace_lines=stacktraces,
            stack_trace_colors=stack_trace_colors,
            args=args
        )
    stack_trace_str = ""
    if 'message' not in string_dict:
        return ""
    message = string_dict['message']
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
            stack_trace_str = clear_stack(stack_trace_map,
                                          pfix,
                                          stack_trace_colors,
                                          log_time,
                                          args=args)
    if len(stack_prefixes) == args.PREV_MSGS_BEFORE_STACK_TRACE:
        stack_trace_map[pfix]["prefixes"] = []
    return stack_trace_str


def assemble_stack_str(
    log_time: str,
    prefix: str,
    stack_trace_prefixes: List[str],
    stack_trace_lines: List[str],
    stack_trace_colors: dict,
    args: dict
):
    # stack_trace_str = args.DIVIDER + "\n"
    stack_trace_str = ""
    if not args.flat:
        stack_trace_str += "\n"

    # Header Line
    back_color, fore_color = stack_trace_colors[prefix]
    stack_trace_str += style(log_time, back_color + Fore.BLACK)
    stack_trace_str += " @ "
    stack_trace_str += style(prefix, fore_color)
    stack_trace_str += "\n"
    # Stack Prefixes

    if not args.flat:
        stack_trace_str += "\n"
    stack_trace_str += style("\n".join([x for x in stack_trace_prefixes if x]),
                             color=Fore.YELLOW)

    biggest_index = len(stack_trace_lines) - 1
    num_stack_traces = min(args.NUM_STACK_TRACES_TO_PRINT, biggest_index)
    continued_str = ""
    if num_stack_traces < biggest_index:
        continued_str = "...continued"
    stack_trace_str += "\n\t"
    stack_trace_str += ("\n\t".join(stack_trace_lines[:num_stack_traces]))
    stack_trace_str += "\n"
    stack_trace_str += (continued_str)
    return stack_trace_str


def clear_stack(
    stack_trace_map: dict,
    pfix: str,
    stack_trace_colors: dict,
    log_time: str,
    args: dict
):
    stack_trace_str = assemble_stack_str(
        log_time=log_time,
        prefix=pfix,
        stack_trace_prefixes=stack_trace_map[pfix]["prefixes"],
        stack_trace_lines=stack_trace_map[pfix]["stacktraces"],
        stack_trace_colors=stack_trace_colors,
        args=args
    )
    stack_trace_map[pfix]["started"] = False
    stack_trace_map[pfix]["prefixes"] = []
    stack_trace_map[pfix]["stacktraces"] = []
    return stack_trace_str

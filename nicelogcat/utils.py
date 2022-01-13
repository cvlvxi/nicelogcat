from functools import reduce
from colorama import init, Fore, Style, Back
import json
import random

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
    Back.BLACK,
    Back.BLUE,
    Back.CYAN,
    Back.GREEN,
    Back.MAGENTA,
    Back.RED,
    Back.WHITE,
    Back.YELLOW,
    Back.LIGHTBLACK_EX,
    Back.LIGHTBLUE_EX,
    Back.LIGHTCYAN_EX,
    Back.LIGHTGREEN_EX,
    Back.LIGHTMAGENTA_EX,
    Back.LIGHTRED_EX,
    Back.LIGHTWHITE_EX,
    Back.LIGHTYELLOW_EX,
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


def flatten_list(l):
    unique = set([x for x in reduce(lambda x, y: x + y, l) if x])

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


def style(val, min_len=None, color=None):
    if not val or not isinstance(val, str):
        return val
    new_val = remove_col_from_val(val)
    new_val_len = len(new_val)
    spacer = " "
    if min_len:
        if new_val_len < min_len:
            new_val = val + spacer * (min_len - new_val_len)
        else:
            raise ValueError(
                "orig_val: {} new_val: {} has length: {} which is bigger than {}".format(
                    val, new_val, new_val_len, min_len
                )
            )
    if color:
        val = color + val + Style.RESET_ALL
    return val


def nested_dicts(some_dict, level=0):
    new_dict = {}
    for k, v in some_dict.items():
        value = None
        try:
            value = json.loads(v)
        except:
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
                key_count, top_spacer, v, key_color, value_color, spacer
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
                    style(k, color=key_color),
                    style(v, color=value_color),
                    args.RIGHT_OF_KEY_VALUE,
                )
            )
            key_count += 1
    if nice_strings:
        nice_str = spacer.join([x for x in nice_strings if x])
    return (key_count, nice_str)


def find_dict_in_v(v, rawline=None):
    if "{" in v and "}" in v:
        first_bracket_idx = v.find("{")
        last_bracket_idx = v.rfind("}")
        json_str = v[first_bracket_idx : last_bracket_idx + 1]
        try:
            val = json.loads(json_str)
            return val
        except Exception as e:
            return {}

    else:
        return {}


def flatten_dict(d):
    new_dict = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict):
                flatten_dict(v)
            else:
                new_dict[k] = v
    return new_dict


def find_stack(stack_trace_map, pfix, message, stack_trace_colors, log_time, args):
    stack_trace_str = ""
    if not pfix or (args.PREFIXES and pfix not in args.PREFIXES):
        return ""
    if pfix not in stack_trace_map:
        stack_trace_map[pfix] = {
            "prefixes": [],
            "stacktraces": [],
            "started": False
            # "flushed": False
        }
        stack_trace_colors[pfix] = args.FORE_COLORS[random.randint(2, 11)]
    message = message.strip()
    is_a_stack_trace = message.startswith("at ")
    if is_a_stack_trace:
        if not stack_trace_map[pfix]["started"]:
            stack_trace_map[pfix]["started"] = True
        stack_trace_map[pfix]["stacktraces"].append(message)
    else:
        stack_trace_map[pfix]["prefixes"].append(message)
        if (
            stack_trace_map[pfix]["started"]
            and len(stack_trace_map[pfix]["stacktraces"]) > 0
        ):
            stack_trace_str = clear_stack(stack_trace_map, pfix, stack_trace_colors, log_time)
    if len(stack_trace_map[pfix]["prefixes"]) == args.PREV_MSGS_BEFORE_STACK_TRACE:
        stack_trace_map[pfix]["prefixes"] = []
    return stack_trace_str


def clear_stack(stack_trace_map, pfix, stack_trace_colors, log_time, args):
    stack_trace_str = args.DIVIDER + "\n"
    stack_trace_str += (
        style(pfix + " : " + log_time, color=stack_trace_colors[pfix]) + "]"
    ) + "\n"
    stack_trace_str += (
        style(
            "\n".join([x for x in stack_trace_map[pfix]["prefixes"] if x]),
            color=Fore.YELLOW,
        )
        + "\n"
    )
    biggest_index = len(stack_trace_map[pfix]["stacktraces"]) - 1
    num_stack_traces = min(args.NUM_STACK_TRACES_TO_PRINT, biggest_index)
    continued_str = ""
    if num_stack_traces < biggest_index:
        continued_str = "...continued"
    stack_trace_str += "\n\t" + (
        "\n\t".join(stack_trace_map[pfix]["stacktraces"][:num_stack_traces])
    ) + "\n"
    stack_trace_str += (continued_str) + "\n"
    stack_trace_map[pfix]["started"] = False
    stack_trace_map[pfix]["prefixes"] = []
    stack_trace_map[pfix]["stacktraces"] = []
    return stack_trace_str

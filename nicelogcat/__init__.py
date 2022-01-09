import sys, os, json, re
import hashlib
import json
import time
from args import args
from colorama import init, Fore, Style, Back
from datetime import datetime
from collections import defaultdict
from prettytable import PrettyTable, FRAME
from constants import COLOR_STRS, FORE_COLORS, BACK_COLORS

FORCE_DISABLE_PRINT = False

COLOR_RESETTERS = [Fore.RESET, Back.RESET, Style.RESET_ALL]

ALL_COLORS = FORE_COLORS + BACK_COLORS + COLOR_RESETTERS


DIVIDER_SIZE = 170

init(autoreset=True)
SUSPENDED = True if args.suspend_util else False
INPUT = open(0, "rb")
# INPUT = sys.stdin
# for line in INPUT:
#     print(line)

DIVIDER = "-" * DIVIDER_SIZE
path_regex = r"(\/.*?\.[\w:]+)"
SKIP_UNTIL_REPEAT = 25
MAX_MEMOIZED_MESSAGES = 200
MEMOIZED_MESSAGES = defaultdict(int)
TIME_SEPARATOR = "\n"
HIGHLIGHT_KEYS = []
HIGHLIGHT_PHRASES = []
IGNORE_KEYS = []
PREFIXES = []
IGNORE_PREFIXES = []
LEVELS = []
FILTERS = []
FILTER_OUT = []
PER_LINE = -1
KEY_COUNT = 1
WILL_COUNT = False
TIMING_SECONDS_INTERVAL = None
COUNTED_LOGS = 0
HEADER_SPACER = None
t0 = time.time()
t1 = None


SPACER = " "
if args.spacer == "newline":
    SPACER = "\n"
elif args.spacer == "space":
    SPACER = " "
elif args.spacer == "tab":
    SPACER = "\t"
elif args.spacer == "pipe":
    SPACER = " | "
else:
    pass

if args.per_line:
    PER_LINE = args.per_line
    print("PER_LINE: {}".format(PER_LINE))
if args.keys:
    HIGHLIGHT_KEYS = args.keys
    print("HIGHLIGHT_KEYS: {}".format([k for k in HIGHLIGHT_KEYS]))
if args.highlight:
    HIGHLIGHT_PHRASES = args.highlight
    print("HIGHLIGHT_PHRASES: {}".format([k for k in HIGHLIGHT_PHRASES]))
if args.ignore_keys:
    IGNORE_KEYS = args.ignore_keys
    print("IGNORE_KEYS: {}".format([k for k in IGNORE_KEYS]))
if args.prefix:
    PREFIXES = args.prefix
    print("PREFIXES: {}".format([k for k in PREFIXES]))
if args.ignore_prefix:
    IGNORE_PREFIXES = args.ignore_prefix
    print("IGNORE_PREFIXES: {}".format([k for k in IGNORE_PREFIXES]))
if args.level:
    LEVELS = args.level
    print("LEVELS: {}".format([k for k in LEVELS]))
if args.filters:
    FILTERS = args.filters
    print("FILTERS: {}".format([k for k in FILTERS]))
if args.filterout:
    FILTER_OUT = args.filterout
    print("FILTER_OUT: {}".format([k for k in FILTER_OUT]))
if args.header_spacer == "newline":
    HEADER_SPACER = "\n"
else:
    HEADER_SPACER = " " * 4
if args.time_per_secs > 0:
    WILL_COUNT = True
    TIMING_SECONDS_INTERVAL = args.time_per_secs
    print("TIMING NUMBER OF LOGS PER: {} seconds".format(TIMING_SECONDS_INTERVAL))


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


def memoize(v, colors):
    global MEMOIZED_MESSAGES
    if len(MEMOIZED_MESSAGES) == MAX_MEMOIZED_MESSAGES:
        print(colors["HIGHLIGHT_COLOR"] + "=" * 50)
        print("Clearing Memozied Messages")
        print(colors["HIGHLIGHT_COLOR"] + "=" * 50)
        MEMOIZED_MESSAGES = defaultdict(int)
    v_hash = hashlib.md5(v.encode()).hexdigest()
    if v_hash not in MEMOIZED_MESSAGES.keys():
        MEMOIZED_MESSAGES[v_hash] += 1
        return (True, 0)
    MEMOIZED_MESSAGES[v_hash] += 1
    curr_count = MEMOIZED_MESSAGES[v_hash]
    if MEMOIZED_MESSAGES[v_hash] % SKIP_UNTIL_REPEAT == 0:
        return (True, curr_count)
    return (False, -1)


def nice_title(title, colors):
    TITLE_DIVS = DIVIDER_SIZE
    TITLE_COLOR = colors["TITLE_COLOR"]
    HALF_DIVS = TITLE_DIVS // 2
    print()
    print(TITLE_COLOR + "=" * TITLE_DIVS)
    if args.title:
        TITLE_LEN = len(title)
        HALF_DIVS_TITLE = HALF_DIVS - TITLE_LEN // 2
        BLANKS = " " * int(HALF_DIVS_TITLE)
        print(TITLE_COLOR + "{}{}{}".format(BLANKS, args.title, BLANKS))
        print(TITLE_COLOR + "=" * TITLE_DIVS)
    print()


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
    key_count, top_spacer, some_dict, key_color, value_color, spacer=SPACER
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
            if IGNORE_KEYS:
                if k in IGNORE_KEYS:
                    continue
            spacer = ""
            if PER_LINE != -1:
                if key_count % PER_LINE == 0:
                    spacer = top_spacer
                else:
                    spacer = ""
            nice_strings.append(
                spacer
                + SPACER
                + "[{}: {}]".format(
                    style(k, color=key_color), style(v, color=value_color)
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


def nice_print(args, fd, colors, rawline):
    global SUSPENDED
    global HEADER_SPACER
    global t0
    global t1
    global COUNTED_LOGS

    V_COLOR = colors["V_COLOR"]

    headers = ["prefix", "level", "log_time"]
    header_line_vals = [fd[k].strip() for k in headers]
    header_pure_val = [remove_col_from_val(x) for x in header_line_vals]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len
    header_line_str = " ".join(header_line_vals) + " " * header_diff + HEADER_SPACER
    total_header_len = header_len + header_diff
    NESTED_SPACER = " "
    TOP_SPACER = "\n{}{}".format(HEADER_SPACER, " " * total_header_len)

    level_val = remove_col_from_val(fd["level"])
    prefix_val = remove_col_from_val(fd["prefix"])

    if args.level and any([level_val not in x for x in LEVELS]):
        return False
    if args.prefix and any([prefix_val not in x for x in PREFIXES]):
        return False
    if args.ignore_prefix and any([prefix_val in x for x in IGNORE_PREFIXES]):
        return False

    string_list = []

    key_order = []
    meta_keys = []

    for k, v in fd.items():
        if isinstance(v, dict):
            meta_keys.append(k)
        if (k not in meta_keys) and (k not in key_order):
            key_order.append(k)
    key_order = sorted(key_order)
    meta_keys = sorted(meta_keys)

    for key in key_order + meta_keys:
        key_count = 0
        k = key
        v = fd[key]
        if IGNORE_KEYS and k in IGNORE_KEYS:
            continue
        if not v:
            continue
        if not k:
            continue

        if k in headers:
            continue
        k = norm_str(k)

        k = style(k, color=colors["K_COLOR"])

        if isinstance(v, dict):
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                TOP_SPACER,
                v,
                key_color=colors["K_COLOR"],
                value_color=colors["V_COLOR"],
                spacer=NESTED_SPACER,
            )
            key_count = new_key_count
            string_list.append(
                "{}:{}{}".format(
                    k,
                    NESTED_SPACER,
                    nice_str,
                )
            )
        else:
            nested_d = find_dict_in_v(v, rawline)
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                TOP_SPACER,
                nested_d,
                key_color=colors["K_COLOR"],
                value_color=colors["V_COLOR"],
                spacer=SPACER,
            )
            key_count = new_key_count
            if nested_d:
                if nice_str:
                    string_list.append(nice_str)

            else:
                string_list.append(
                    "[{}: {}]".format(k, style(v, color=colors["V_COLOR"]))
                )
    if args.raw:
        string_list.append(
            "[{}: {}]".format(
                style("rawline", color=colors["K_COLOR"]),
                style(rawline, color=colors["V_COLOR"]),
            )
        )

    will_print = True
    result_str = SPACER.join([x for x in string_list if x])
    result_str_no_col = remove_col_from_val(result_str)

    if HIGHLIGHT_PHRASES:
        for phrase in set(HIGHLIGHT_PHRASES):
            if phrase in result_str:
                result_str = result_str.replace(
                    phrase, style(phrase, color=colors["HIGHLIGHT_COLOR"])
                )
    if FILTERS:
        if args.filter_all:
            will_print = all([f.lower() in result_str_no_col.lower() for f in FILTERS])
        else:
            will_print = any([f.lower() in result_str_no_col.lower() for f in FILTERS])
    if FILTER_OUT:
        will_print = not any([f in result_str_no_col for f in FILTER_OUT])
    if SUSPENDED:
        will_print = False
        if not args.suspend_util:
            raise ValueError("Suspended by no suspend-util supplied")
        if args.suspend_util in result_str_no_col:
            SUSPENDED = False
            will_print = True
            print("Found suspend_util, will continue")
    if will_print:
        if WILL_COUNT:
            COUNTED_LOGS += 1
            t1 = time.time()
            if (t1 - t0) >= TIMING_SECONDS_INTERVAL:
                t0 = t1
                print(
                    style(
                        "Number of logs after {} seconds: {}".format(
                            TIMING_SECONDS_INTERVAL, COUNTED_LOGS
                        ),
                        color=colors["TIMING_COLOR"],
                    )
                )
                COUNTED_LOGS = 0
        if args.divider:
            print(style(DIVIDER, color=colors["DIVIDER_STYLE"]))
            if args.linespace > 0:
                print()

        if FORCE_DISABLE_PRINT:
            return True
        # THE PRINT
        if args.title and args.show_title_every_line:
            timing_title = (
                "🕒 ({} secs) ".format(TIMING_SECONDS_INTERVAL) if WILL_COUNT else ""
            )
            print(
                style(
                    "[{}{}]".format(timing_title, args.title),
                    color=BACK_COLORS[COLOR_STRS.index(args.title_line_color)]
                    + Fore.BLACK,
                )
            )
        print(header_line_str + " " + result_str)
        return True
    return False


def main_loop(args, colors):

    while True:
        line = next(INPUT)
        line = line.decode(errors="ignore")
        line = line.strip()
        if not line:
            continue
        parts = [x for x in line.split(" ") if x]
        if parts[0] == "---------":
            continue

        date = norm_str3(parts[0])
        timestamp = norm_str3(parts[1])
        pid = norm_str3(parts[2])
        log_level = get_log_level(norm_str3(parts[4]), colors)
        prefix = norm_str3(parts[5]).strip()
        msg = norm_str3(" ".join(parts[6:]))

        # current_time = datetime.now().strftime("%m-%d %H:%M:%S")
        log_time = style(date + " " + timestamp, color=colors["TIME_COLOR"], min_len=20)
        the_keys = ["level", "prefix", "log_time", "pid", "message"]
        the_values = [
            style(log_level, min_len=10),
            # style(current_time, color=colors["CURRENT_TIME_COLOR"], min_len=20),
            style(prefix, color=colors["PREFIX_COLOR"], min_len=70),
            log_time,
            pid,
            msg,
        ]
        the_dict = dict(zip(the_keys, the_values))
        fd = nested_dicts(the_dict)
        printed = nice_print(args, fd, colors, rawline=line)
        if printed:
            for i in range(args.linespace):
                print()


def main():
    colors = {
        "HEADER_STR_COLOR": Back.YELLOW + Fore.BLACK,
        "LEVEL_WARN_COLOR": Back.BLACK + Fore.YELLOW,
        "LEVEL_ERROR_COLOR": Back.BLACK + Fore.RED,
        "LEVEL_INFO_COLOR": Back.BLACK + Fore.GREEN,
        "TIME_COLOR": Fore.MAGENTA,
        "CURRENT_TIME_COLOR": Fore.RED,
        "PREFIX_COLOR": Fore.GREEN,
        "TITLE_COLOR": Fore.MAGENTA,
        "HIGHLIGHT_COLOR": Fore.BLACK + Back.GREEN,
        "V_COLOR": Fore.WHITE,
        "K_COLOR": Fore.CYAN,
        "STACK_MSG_COLOR": Fore.GREEN,
        "PATH_COLOR": Fore.LIGHTMAGENTA_EX,
        "TIMING_COLOR": Back.RED + Fore.BLACK,
        "DIVIDER_STYLE": Fore.CYAN,
    }
    nice_title(args.title, colors)
    main_loop(args, colors)


if __name__ == "__main__":
    main()

import json
import argparse
import hashlib
import json
from colorama import init, Fore, Style, Back
from collections import defaultdict

FORE_COLORS = [
    Fore.BLACK,
    Fore.BLUE,
    Fore.CYAN,
    Fore.GREEN,
    Fore.MAGENTA,
    Fore.RED,
    Fore.WHITE,
    Fore.YELLOW,
    Fore.LIGHTBLACK_EX,
    Fore.LIGHTBLUE_EX,
    Fore.LIGHTCYAN_EX,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTMAGENTA_EX,
    Fore.LIGHTRED_EX,
    Fore.LIGHTWHITE_EX,
    Fore.LIGHTYELLOW_EX,
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

COLOR_RESETTERS = [Fore.RESET, Back.RESET, Style.RESET_ALL]

ALL_COLORS = FORE_COLORS + BACK_COLORS + COLOR_RESETTERS

parser = argparse.ArgumentParser(description="Bleh")
parser.add_argument("--title", default="", type=str, help="Title to show")
parser.add_argument("--suspend-util", default=None, type=str, help="Suspend until this is found")
parser.add_argument(
    "--spacer",
    default="space",
    choices=["newline", "space", "tab", "pipe"],
    help="spacer to use",
)
parser.add_argument(
    "--linespace", type=int, default=0, help="Number of spaces between lines"
)
parser.add_argument("--divider", action="store_true", help="Add a divider per line")
parser.add_argument("--raw", action="store_true", help="Include raw line")
parser.add_argument(
    "--keys", nargs="*", required=False, default=None, help="Highlight keys"
)
parser.add_argument(
    "--highlight",
    nargs="*",
    required=False,
    default=None,
    help="Highlight these phrase",
)
parser.add_argument(
    "--filters", nargs="*", default=None, type=str, help="List of filters"
)
parser.add_argument(
    "--level", nargs="*", default=None, type=str, help="Only these levels"
)
parser.add_argument(
    "--prefix", nargs="*", default=None, type=str, help="Only these Prefix"
)
parser.add_argument(
    "--ignore-prefix", nargs="*", default=None, type=str, help="Ignore These Prefix"
)
parser.add_argument(
    "--filterout",
    nargs="*",
    default=None,
    type=str,
    help="List of filters to filter out",
)

args = parser.parse_args()

DIVIDER_SIZE = 60

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


def nice_print_dict(some_dict, key_color, value_color, spacer=SPACER):
    nice_str = ""
    nice_strings = []
    for k, v in some_dict.items():
        if isinstance(v, dict):
            nice_strings.append(nice_print_dict(v, key_color, value_color, spacer))
        else:
            nice_strings.append(
                "[{}: {}]".format(style(k, color=key_color), style(v, color=value_color))
            )
    if nice_strings:
        nice_str = spacer.join(nice_strings)
    return nice_str


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
    HIGHLIGHT_KEYS = args.keys if args.keys else []
    HIGHLIGHT_PHRASES = args.highlight if args.highlight else []
    FILTERS = args.filters if args.filters else []
    PREFIXES = args.prefix if args.prefix else []
    IGNORE_PREFIXES = args.ignore_prefix if args.ignore_prefix else []
    LEVELS = args.level if args.level else []
    FILTER_OUT = args.filterout if args.filterout else []
    V_COLOR = colors["V_COLOR"]
    NESTED_SPACER = "\n{}".format(" " * 4) if SPACER == '\n' else ' '

    headers = ["prefix", "level", "log_time"]
    header_line_vals = [fd[k].strip() for k in headers]
    HEADER_SPACER = " "*2
    header_pure_val = [remove_col_from_val(x) for x in header_line_vals]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len
    # header_line_vals = [style(x, color=Back.BLACK) for x in header_line_vals]
    header_line_str = " ".join(header_line_vals) + " " * header_diff + HEADER_SPACER
    total_header_len = header_len + header_diff
    NESTED_SPACER = " "
    TOP_SPACER = "\n{}{}".format(HEADER_SPACER, " "*total_header_len)


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
        k = key
        v = fd[key]

        if not v:
            continue
        if not k:
            continue

        if k in headers:
            continue
        k = norm_str(k)
        k = style(k, color=colors["K_COLOR"])

        if isinstance(v, dict):
            # top_spacer = "\n" if SPACER == " " else ""
            top_spacer = TOP_SPACER
            string_list.append(
                "{}{}:{}{}".format(
                    top_spacer,
                    k,
                    NESTED_SPACER,
                    nice_print_dict(
                        v,
                        key_color=colors["K_COLOR"],
                        value_color=colors["V_COLOR"],
                        spacer=NESTED_SPACER,
                    ),
                )
            )
        else:
            nested_d = find_dict_in_v(v, rawline)
            if nested_d:
                string_list.append(
                    nice_print_dict(
                        nested_d,
                        key_color=colors["K_COLOR"],
                        value_color=colors["V_COLOR"],
                        spacer=SPACER,
                    )
                )

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
    result_str = SPACER.join(string_list)


    if HIGHLIGHT_PHRASES:
        for phrase in set(HIGHLIGHT_PHRASES):
            if phrase in result_str:
                result_str = result_str.replace(
                    phrase, colors["HIGHLIGHT_COLOR"] + phrase #+ Style.RESET_ALL
                )
    if FILTERS:
        will_print = any([f in rawline for f in FILTERS])
    if FILTER_OUT:
        will_print = not any([f in rawline for f in FILTER_OUT])
    if SUSPENDED:
        will_print = False
        if not args.suspend_util: raise ValueError("Suspended by no suspend-util suppied")
        if args.suspend_util in rawline:
            SUSPENDED = False
            will_print = True
            print("Found suspend_util, will continue")

    if will_print:
        if args.divider:
            print(DIVIDER)
        print(header_line_str + result_str)
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

        log_time = style(date + " " + timestamp, color=colors["TIME_COLOR"], min_len=20)
        the_keys = ["level", "prefix", "log_time", "pid", "message"]
        the_values = [
            style(log_level, min_len=10),
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
        "HIGHLIGHT_COLOR": Back.BLACK + Fore.GREEN,
        "V_COLOR": Fore.WHITE,
        "K_COLOR": Fore.CYAN,
        "STACK_MSG_COLOR": Fore.GREEN,
        "PATH_COLOR": Fore.LIGHTMAGENTA_EX,
    }
    nice_title(args.title, colors)
    main_loop(args, colors)


# if __name__ == "__main__":
#     main()

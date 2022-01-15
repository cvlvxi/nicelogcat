import time
from typing import Tuple, Optional
from colorama import init, Fore, Back
from nicelogcat.utils import *

TITLE = ""
init(autoreset=True)


def nice_print(
    args: dict,
    linedict: dict,
    rawline: str,
    force_disable_print: bool,
    is_recording: bool
) -> Tuple[Optional[str], bool]:
    global HEADER_SPACER
    global COUNTED_LOGS
    global PREV_RECORDED_STRING_DICT

    headers = ["prefix", "level", "log_time"]
    header_line_vals = [linedict[k].strip() for k in headers]
    header_pure_val = [remove_col_from_val(x) for x in header_line_vals]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len
    header_line_str = " ".join(header_line_vals) + \
        " " * header_diff + args.HEADER_SPACER
    if args.flat:
        header_line_str = " ".join(header_line_vals)
    total_header_len = header_len + header_diff
    NESTED_SPACER = " "
    TOP_SPACER = (
        "\n{}{}".format(args.HEADER_SPACER, " " *
                        total_header_len) if (not args.flat or args.no_flat) else " "
    )

    level_val = remove_col_from_val(linedict["level"])
    prefix_val = remove_col_from_val(linedict["prefix"])

    if args.level and any([level_val not in x for x in args.LEVELS]):
        return ("", False)
    if args.PREFIXES and all([prefix_val.strip().lower() != x.lower() for x in args.PREFIXES]) or not prefix_val:
        return ("", False)
    if args.ignore_prefix and any([prefix_val in x for x in args.IGNORE_PREFIXES]):
        return ("", False)

    string_list = []

    key_order = []
    meta_keys = []

    for k, v in linedict.items():
        if isinstance(v, dict):
            meta_keys.append(k)
        if (k not in meta_keys) and (k not in key_order):
            key_order.append(k)
    key_order = sorted(key_order)
    meta_keys = sorted(meta_keys)

    string_dict = {}

    for key in key_order + meta_keys:
        key_count = 0
        k = key
        v = linedict[key]

        if args.IGNORE_KEYS and k in args.IGNORE_KEYS:
            continue
        if not v:
            continue
        if not k:
            continue

        if k in headers:
            continue
        k = norm_str(k)
        non_color_k = k
        k = style(k, color=args.colors["K_COLOR"])

        if isinstance(v, dict):
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                TOP_SPACER,
                v,
                key_color=args.colors["K_COLOR"],
                value_color=args.colors["V_COLOR"],
                args=args
            )
            key_count = new_key_count
            string_list.append(
                "{}:{}{}".format(
                    k,
                    NESTED_SPACER,
                    nice_str,
                )
            )
            nested_d = find_dict_in_v(v, rawline)
            if nested_d:
                string_dict.update(flatten_dict(nested_d))
            else:
                string_dict[non_color_k] = v
        else:
            nested_d = find_dict_in_v(v, rawline)
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                TOP_SPACER,
                nested_d,
                key_color=args.colors["K_COLOR"],
                value_color=args.colors["V_COLOR"],
                args=args
            )
            key_count = new_key_count
            if nested_d:
                if nice_str:
                    string_list.append(nice_str)
                string_dict.update(flatten_dict(nested_d))

            else:
                string_dict[non_color_k] = v
                string_list.append(
                    "{}{}: {}{}".format(
                        args.LEFT_OF_KEY_VALUE,
                        k,
                        style(v, color=args.colors["V_COLOR"]),
                        args.RIGHT_OF_KEY_VALUE,
                    )
                )

    if args.raw:
        string_list.append(
            "[{}: {}]".format(
                style("rawline", color=args.colors["K_COLOR"]),
                style(rawline, color=args.colors["V_COLOR"]),
            )
        )
    will_print = True
    result_str = args.SPACER.join([x for x in string_list if x])
    result_str_no_col = remove_col_from_val(result_str)

    string_dict = flatten_dict(string_dict)

    changed_keys = []
    change_detected = False
    if force_disable_print or args.disable:
        will_print = False

    if args.RECORD_KEYS_DIFF:
        for key in args.RECORD_KEYS_DIFF:
            if key in string_dict and key not in args.PREV_RECORDED_STRING_DICT:
                args.PREV_RECORDED_STRING_DICT[key] = string_dict[key]
            if key in string_dict and string_dict[key] != args.PREV_RECORDED_STRING_DICT[key]:
                changed_keys.append(key)
                change_detected = True
        # Highlight keys
        for key in changed_keys:
            result_str = result_str.replace(
                key, style(key, color=args.colors["DETECTED_CHANGE_COLOR"])
            )
        # Update
        for key in string_dict:
            args.PREV_RECORDED_STRING_DICT[key] = string_dict[key]

    if args.RECORD_KEYS_DIFF and not change_detected:
        will_print = False
        return ('', False)

    if args.HIGHLIGHT_PHRASES:
        for phrase in set(args.HIGHLIGHT_PHRASES):
            if phrase in result_str:
                result_str = result_str.replace(
                    phrase, style(phrase, color=args.colors["HIGHLIGHT_COLOR"])
                )
    if args.FILTERS:
        if args.filter_any or args.any:
            will_print = any([f.lower() in result_str_no_col.lower()
                             for f in args.FILTERS])
        else:
            will_print = all([f.lower() in result_str_no_col.lower()
                             for f in args.FILTERS])
    if args.FILTER_OUT:
        if will_print:
            will_print = not any([f in result_str_no_col.lower()
                                 for f in args.FILTER_OUT])
    count_str = ""
    if will_print:
        if args.WILL_COUNT:
            args.COUNTED_LOGS += 1
            args.t1 = time.time()
            if (args.t1 - args.t0) >= args.TIMING_SECONDS_INTERVAL:
                args.t0 = args.t1
                count_str = (
                    style(
                        "Number of logs after {} seconds: {}".format(
                            args.TIMING_SECONDS_INTERVAL, args.COUNTED_LOGS
                        ),
                        color=args.colors["TIMING_COLOR"],
                    )
                    + "\n"
                )
                COUNTED_LOGS = 0
        divider_str = ""
        if args.divider:
            divider_str = args.DIVIDER + "\n"

        if args.title and args.show_title_every_line:
            timing_title = (
                "🕒 ({} secs) ".format(
                    args.TIMING_SECONDS_INTERVAL) if args.WILL_COUNT else ""
            )
            title_str = style(
                "[{}{}]".format(timing_title, args.title),
                color=Back.GREEN + Fore.BLACK,
            )
            header_line_str = title_str + "\n" + header_line_str
        if args.ALLOW_RECORD and is_recording:
            header_line_str = "🟢" + " " + header_line_str
        if args.ALLOW_RECORD and not is_recording:
            header_line_str = "🔴" + " " + header_line_str

        # THE PRINT
        thing_to_print = (
            divider_str + count_str + header_line_str +
            TOP_SPACER + args.SPACER + result_str
        )
        if args.flat and not args.no_flat:
            thing_to_print = count_str + header_line_str + args.SPACER + result_str.strip()
        return (thing_to_print, change_detected)
    return ("", False)

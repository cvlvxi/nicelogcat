import time
import os
import nicelogcat.utils as utils
from typing import Tuple, Optional
from colorama import init, Fore, Back
from pynput import keyboard
from traceback import print_exc
from typing import BinaryIO


init(autoreset=True)
INIT_NOT_RECORDING_STATE = True
RECORD_KEY = keyboard.Key.f12
RECORD_FILE_NAME = None
RECORD_DIR = ""
FORCE_DISABLE_PRINT = False
IS_RECORDING = False
TITLE = ""
STACK_TRACE_MAP = {}
STACK_TRACE_COLORS = {}


async def main_loop(args: dict, stream: BinaryIO):
    global TITLE
    global RECORD_DIR
    RECORD_DIR = args.record_dir
    TITLE = args.title.lower().replace(" ", "_") if args.title else ""
    try:
        while True:
            line = next(stream)
            line = line.decode(errors="ignore")
            line = line.strip()
            if not line:
                continue
            parts = [x for x in line.split(" ") if x]
            if parts[0] == "---------":
                continue
            date = utils.norm_str3(parts[0])
            timestamp = utils.norm_str3(parts[1])
            pid = utils.norm_str3(parts[2])
            log_level = utils.get_log_level(utils.norm_str3(parts[4]),
                                            args.colors)
            prefix = utils.norm_str3(parts[5]).strip()
            msg = utils.norm_str3(" ".join(parts[6:]))
            log_time = utils.style(date + " " + timestamp,
                                   color=args.colors["TIME_COLOR"])
            the_keys = ["level", "prefix", "log_time", "pid", "message"]
            the_values = [
                log_level,
                utils.style(prefix, color=args.colors["PREFIX_COLOR"]),
                log_time,
                pid,
                msg,
            ]
            linedict = utils.nested_dicts(dict(zip(the_keys, the_values)))
            (thing_to_print, change_detected) = nice_print(
                args,
                linedict,
                rawline=line,
                force_disable_print=FORCE_DISABLE_PRINT,
                is_recording=IS_RECORDING,
            )
            if not thing_to_print:
                continue
            if FORCE_DISABLE_PRINT or args.disable:
                continue
            # THE PRINT
            # Stack trace here
            # if stack_trace_str:
            #     thing_to_print = stack_trace_str + "\n" + thing_to_print
            # if args.linespace > 1:
            #     thing_to_print = thing_to_print + "\n" * args.linespace
            # CAPTURE RECORDING TO FILE
            if args.ALLOW_RECORD and IS_RECORDING:
                record_file_path = os.path.join(
                    args.RECORD_DIR, RECORD_FILE_NAME)
                write_to_file = True
                if args.RECORD_KEYS_DIFF:
                    write_to_file = change_detected
                with open(record_file_path, "a") as f:
                    if write_to_file:
                        f.write(thing_to_print + "\n")
            yield thing_to_print

    except StopIteration:
        pass
    except KeyboardInterrupt:
        import sys
        sys.exit(1)
    except Exception:
        print_exc()


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
    header_pure_val = [utils.remove_col_from_val(x) for x in header_line_vals]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len
    header_line_str = " ".join(header_line_vals) + " " *  \
        header_diff + args.HEADER_SPACER
    if args.flat:
        header_line_str = " ".join(header_line_vals)
    total_header_len = header_len + header_diff
    NESTED_SPACER = " "
    TOP_SPACER = ("\n{}{}".format(args.HEADER_SPACER, " " *
                  total_header_len) if (not args.flat or args.no_flat)
                  else " ")

    level_val = utils.remove_col_from_val(linedict["level"])
    prefix_val = utils.remove_col_from_val(linedict["prefix"])
    log_time = utils.remove_col_from_val(linedict["log_time"])

    if args.level and any([level_val not in x for x in args.LEVELS]):
        return ("", False)
    prefix_exists_check = [prefix_val.strip().lower() != x.lower()
                           for x in args.PREFIXES]
    if args.PREFIXES and all(prefix_exists_check) or not prefix_val:
        return ("", False)
    ignore_prefix_check = [prefix_val in x for x in args.IGNORE_PREFIXES]
    if args.ignore_prefix and any(ignore_prefix_check):
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
        k = utils.norm_str(k)
        non_color_k = k
        k = utils.style(k, color=args.colors["K_COLOR"])

        if isinstance(v, dict):
            (new_key_count, nice_str) = utils.nice_print_dict(
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
            nested_d = utils.find_dict_in_v(v, rawline)
            if nested_d:
                string_dict.update(utils.flatten_dict(nested_d))
            else:
                string_dict[non_color_k] = v
        else:
            nested_d = utils.find_dict_in_v(v, rawline)
            (new_key_count, nice_str) = utils.nice_print_dict(
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
                string_dict.update(utils.flatten_dict(nested_d))

            else:
                string_dict[non_color_k] = v
                string_list.append(
                    "{}{}: {}{}".format(
                        args.LEFT_OF_KEY_VALUE,
                        k,
                        utils.style(v, color=args.colors["V_COLOR"]),
                        args.RIGHT_OF_KEY_VALUE,
                    )
                )

    if args.raw:
        string_list.append(
            "[{}: {}]".format(
                utils.style("rawline", color=args.colors["K_COLOR"]),
                utils.style(rawline, color=args.colors["V_COLOR"]),
            )
        )
    stack_trace_str = ""
    # Stack Traces
    if args.FIND_STACKTRACES:
        global STACK_TRACE_COLORS
        global STACK_TRACE_MAP
        run_find_stack = True
        if args.PREFIXES:
            run_find_stack = prefix_val.lower(
            ) in [p.lower() for p in args.PREFIXES]
        if args.IGNORE_PREFIXES:
            run_find_stack = not (prefix_val.lower() in [
                                  p.lower() for p in args.IGNORE_PREFIXES])
        if run_find_stack:
            stack_trace_str = utils.find_stack(STACK_TRACE_MAP,
                                               prefix_val,
                                               string_dict,
                                               STACK_TRACE_COLORS,
                                               log_time,
                                               args=args)
            if stack_trace_str:
                print(stack_trace_str)
    will_print = True
    result_str = args.SPACER.join([x for x in string_list if x])
    result_str_no_col = utils.remove_col_from_val(result_str)

    string_dict = utils.flatten_dict(string_dict)

    changed_keys = []
    change_detected = False
    if force_disable_print or args.disable:
        will_print = False

    if args.RECORD_KEYS_DIFF:
        for key in args.RECORD_KEYS_DIFF:
            if key in string_dict and key not in \
                    args.PREV_RECORDED_STRING_DICT:
                args.PREV_RECORDED_STRING_DICT[key] = string_dict[key]
            if key in string_dict and string_dict[key] != \
                    args.PREV_RECORDED_STRING_DICT[key]:
                changed_keys.append(key)
                change_detected = True
        # Highlight keys
        for key in changed_keys:
            result_str = result_str.replace(
                key, utils.style(
                    key,
                    color=args.colors["DETECTED_CHANGE_COLOR"])
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
                    phrase, utils.style(
                        phrase,
                        color=args.colors["HIGHLIGHT_COLOR"])
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
                    utils.style(
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
            title_str = utils.style(
                "[{}{}]".format(timing_title, args.title),
                color=Back.GREEN + Fore.BLACK,
            )
            header_line_str = title_str + " " + header_line_str
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
            thing_to_print = count_str + \
                             header_line_str + \
                             args.SPACER + \
                             result_str.strip()
        return (thing_to_print, change_detected)
    return ("", False)


def on_press(key):
    global IS_RECORDING
    global INIT_NOT_RECORDING_STATE
    global RECORD_FILE_NAME
    global TITLE
    set_filename = False
    try:
        if key == RECORD_KEY:
            IS_RECORDING = not IS_RECORDING
            INIT_NOT_RECORDING_STATE = False
            if not INIT_NOT_RECORDING_STATE and IS_RECORDING:
                if not TITLE:
                    TITLE = os.path.dirname(os.getcwd())
                set_filename = True
            if not INIT_NOT_RECORDING_STATE and not IS_RECORDING:
                set_filename = True
            if set_filename:
                curr_files = [
                    int(x.rsplit('.log')[0].rsplit('_')[-1])
                    for x in os.listdir(RECORD_DIR)
                    if TITLE in x
                ]
                curr_files = sorted(curr_files)
                next_inc = 0
                if curr_files:
                    next_inc = int(curr_files[-1]) + 1
                RECORD_FILE_NAME = TITLE + "_{}.log".format(next_inc)
    except AttributeError:
        pass

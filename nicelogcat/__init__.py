import os
import json
import time
from pynput import keyboard
from colorama import init, Fore, Back
from nicelogcat.utils import *
from nicelogcat.args import get_args
from traceback import print_exc

FORCE_DISABLE_PRINT = False

IS_RECORDING = False
INIT_NOT_RECORDING_STATE = True
RECORD_KEY = keyboard.Key.f12
RECORD_FILE_NAME = None
RECORD_DIR = ""
TITLE = ""
init(autoreset=True)
INPUT = open(0, "rb")
# INPUT = sys.stdin
# for line in INPUT:
#     print(line)


def nice_print(args, fd, colors, rawline):
    global HEADER_SPACER
    global t0
    global t1
    global COUNTED_LOGS
    global PREV_RECORDED_STRING_DICT

    headers = ["prefix", "level", "log_time"]
    header_line_vals = [fd[k].strip() for k in headers]
    header_pure_val = [remove_col_from_val(x) for x in header_line_vals]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len
    header_line_str = " ".join(header_line_vals) + " " * header_diff + args.HEADER_SPACER
    if args.flat:
        header_line_str = " ".join(header_line_vals)
    total_header_len = header_len + header_diff
    NESTED_SPACER = " "
    TOP_SPACER = (
        "\n{}{}".format(args.HEADER_SPACER, " " * total_header_len) if (not args.flat or args.no_flat) else " "
    )

    level_val = remove_col_from_val(fd["level"])
    prefix_val = remove_col_from_val(fd["prefix"])

    if args.level and any([level_val not in x for x in args.LEVELS]):
        return ("", False)
    if args.PREFIXES and all([prefix_val.strip().lower() != x.lower() for x in args.PREFIXES]) or not prefix_val:
        return ("", False)
    if args.ignore_prefix and any([prefix_val in x for x in args.IGNORE_PREFIXES]):
        return ("", False)

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

    string_dict = {}

    for key in key_order + meta_keys:
        key_count = 0
        k = key
        v = fd[key]

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
        k = style(k, color=colors["K_COLOR"])

        if isinstance(v, dict):
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                TOP_SPACER,
                v,
                key_color=colors["K_COLOR"],
                value_color=colors["V_COLOR"],
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
                key_color=colors["K_COLOR"],
                value_color=colors["V_COLOR"],
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
                        style(v, color=colors["V_COLOR"]),
                        args.RIGHT_OF_KEY_VALUE,
                    )
                )

    if args.raw:
        string_list.append(
            "[{}: {}]".format(
                style("rawline", color=colors["K_COLOR"]),
                style(rawline, color=colors["V_COLOR"]),
            )
        )
    will_print = True
    result_str = args.SPACER.join([x for x in string_list if x])
    result_str_no_col = remove_col_from_val(result_str)

    string_dict = flatten_dict(string_dict)

    changed_keys = []
    change_detected = False
    if FORCE_DISABLE_PRINT or args.disable:
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
                key, style(key, color=colors["DETECTED_CHANGE_COLOR"])
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
                    phrase, style(phrase, color=colors["HIGHLIGHT_COLOR"])
                )
    if args.FILTERS:
        if args.filter_any or args.any:
            will_print = any([f.lower() in result_str_no_col.lower() for f in args.FILTERS])
        else:
            will_print = all([f.lower() in result_str_no_col.lower() for f in args.FILTERS])
    if args.FILTER_OUT:
        if will_print:
            will_print = not any([f in result_str_no_col.lower() for f in args.FILTER_OUT])
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
                        color=colors["TIMING_COLOR"],
                    )
                    + "\n"
                )
                COUNTED_LOGS = 0
        divider_str = ""
        if args.divider:
            divider_str = args.DIVIDER + "\n"

        if args.title and args.show_title_every_line:
            timing_title = (
                "🕒 ({} secs) ".format(args.TIMING_SECONDS_INTERVAL) if args.WILL_COUNT else ""
            )
            title_str = style(
                "[{}{}]".format(timing_title, args.title),
                color=Back.GREEN + Fore.BLACK,
            )
            header_line_str = title_str + "\n" + header_line_str
        if args.ALLOW_RECORD and IS_RECORDING:
            header_line_str = "🟢" + " " + header_line_str
        if args.ALLOW_RECORD and not IS_RECORDING:
            header_line_str = "🔴" + " " + header_line_str

        # THE PRINT
        thing_to_print = (
            divider_str + count_str + header_line_str + TOP_SPACER + args.SPACER + result_str
        )
        if args.flat and not args.no_flat:
            thing_to_print = count_str + header_line_str + args.SPACER + result_str.strip()
        return (thing_to_print, change_detected)
    return ("", False)


def main_loop(args, colors):
    try:
        # MESSAGE_BUFFER = []
        # MESSAGE_BUFFER_SIZE = 2000
        STACK_TRACE_MAP = {}
        STACK_TRACE_COLORS = {}
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
            stack_trace_str = ""
            # Stack Traces
            if args.FIND_STACKTRACES:
                run_find_stack = True
                if args.PREFIXES:
                    run_find_stack = prefix.lower() in [p.lower() for p in args.PREFIXES]
                if args.IGNORE_PREFIXES:
                    run_find_stack = not (
                        prefix.lower() in [p.lower() for p in args.IGNORE_PREFIXES]
                    )
                if run_find_stack:
                    stack_trace_str = find_stack(
                        STACK_TRACE_MAP, prefix, msg, STACK_TRACE_COLORS, log_time, args=args
                    )
            the_dict = dict(zip(the_keys, the_values))
            fd = nested_dicts(the_dict)
            (thing_to_print, change_detected) = nice_print(args, fd, colors, rawline=line)
            if not thing_to_print:
                continue
            if FORCE_DISABLE_PRINT or args.disable:
                continue
            # THE PRINT
            if stack_trace_str:
                thing_to_print = stack_trace_str + "\n" + thing_to_print
            if args.linespace > 1:
                thing_to_print = thing_to_print + "\n" * args.linespace
            # if len(MESSAGE_BUFFER) == MESSAGE_BUFFER_SIZE:
            #     MESSAGE_BUFFER = []
            # MESSAGE_BUFFER.append(thing_to_print)
            # print(MESSAGE_BUFFER[-1])
            print(thing_to_print)

            # CAPTURE RECORDING TO FILE
            if args.ALLOW_RECORD and IS_RECORDING:
                record_file_path = os.path.join(args.RECORD_DIR, RECORD_FILE_NAME)
                write_to_file = True
                if args.RECORD_KEYS_DIFF:
                    write_to_file = change_detected
                with open(record_file_path, "a") as f:
                    if write_to_file:
                        f.write(thing_to_print + "\n")
    except:
        print_exc();

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




def main():
    global RECORD_DIR
    global TITLE
    args = get_args()
    RECORD_DIR = args.RECORD_DIR
    TITLE = args.title.lower().replace(" ", "_") if args.title else ""
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
        "TIMING_COLOR": Back.RED + Fore.BLACK,
        "DETECTED_CHANGE_COLOR": Back.RED + Fore.BLACK,
    }
    if args.ALLOW_RECORD:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                main_loop(args, colors)
                listener.join()
            except:
                pass
    else:
        main_loop(args, colors)


if __name__ == "__main__":
    main()

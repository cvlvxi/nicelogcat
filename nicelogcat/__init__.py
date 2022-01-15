import os
from pynput import keyboard
from traceback import print_exc
from colorama import Fore, Back
from nicelogcat.logcat import nice_print
from nicelogcat.args import get_args
from nicelogcat.utils import *

INIT_NOT_RECORDING_STATE = True
RECORD_KEY = keyboard.Key.f12
RECORD_FILE_NAME = None
RECORD_DIR = ""
FORCE_DISABLE_PRINT = False
IS_RECORDING = False
INPUT = open(0, "rb")
# INPUT = sys.stdin
# for line in INPUT:
#     print(line)


def main_loop(args: dict):
    try:
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
            log_level = get_log_level(norm_str3(parts[4]), args.colors)
            prefix = norm_str3(parts[5]).strip()
            msg = norm_str3(" ".join(parts[6:]))
            log_time = style(date + " " + timestamp,
                             color=args.colors["TIME_COLOR"], min_len=20)
            the_keys = ["level", "prefix", "log_time", "pid", "message"]
            the_values = [
                style(log_level, min_len=10),
                style(prefix, color=args.colors["PREFIX_COLOR"], min_len=70),
                log_time,
                pid,
                msg,
            ]
            stack_trace_str = ""
            # Stack Traces
            if args.FIND_STACKTRACES:
                run_find_stack = True
                if args.PREFIXES:
                    run_find_stack = prefix.lower() in [
                        p.lower() for p in args.PREFIXES]
                if args.IGNORE_PREFIXES:
                    run_find_stack = not (
                        prefix.lower() in [p.lower()
                                           for p in args.IGNORE_PREFIXES]
                    )
                if run_find_stack:
                    stack_trace_str = find_stack(
                        STACK_TRACE_MAP, prefix, msg, STACK_TRACE_COLORS, log_time, args=args
                    )
            linedict = nested_dicts(dict(zip(the_keys, the_values)))
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
            if stack_trace_str:
                thing_to_print = stack_trace_str + "\n" + thing_to_print
            if args.linespace > 1:
                thing_to_print = thing_to_print + "\n" * args.linespace
            print(thing_to_print)

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
    except:
        print_exc()


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
    args.colors = colors
    # if args.ALLOW_RECORD:
    #     with keyboard.Listener(on_press=on_press) as listener:
    #         try:
    #             main_loop(args)
    #             listener.join()
    #         except:
    #             pass
    # else:
    main_loop(args)


if __name__ == "__main__":
    main()

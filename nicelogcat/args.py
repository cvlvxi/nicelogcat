
import argparse
import time
import os
from pynput import keyboard
from colorama import init, Fore, Style, Back
from nicelogcat.utils import *
from collections import defaultdict


SHOW_ARGS = False



def get_args():
    parser = argparse.ArgumentParser(description="nicelogcat")
    parser.add_argument(dest="filterz", nargs="*", type=str, help="List of filters")
    parser.add_argument("--title", default="", type=str, help="Title to show")
    parser.add_argument(
        "--suspend-util", default=None, type=str, help="Suspend until this is found"
    )
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
    parser.add_argument("--disable", action="store_true", help="Disable Print")
    parser.add_argument("--flat", action="store_true", help="Flat")
    parser.add_argument(
        "--title-in-header", action="store_true", help="Add title to header"
    )
    parser.add_argument("--raw", action="store_true", help="Include raw line")
    parser.add_argument(
        "--show-title-every-line", action="store_true", help="Show title every line"
    )
    parser.add_argument(
        "--title-line-color",
        default=Fore.BLUE,
        choices=COLOR_STRS,
        help="Color to use if showing title every line",
    )
    parser.add_argument("--per-line", type=int, default=4, help="Keys per line")
    parser.add_argument(
        "--time-per-secs",
        type=int,
        default=0,
        help="Will time how many logs called every [internal] secs",
    )

    parser.add_argument(
        "--header-spacer",
        default="space",
        choices=["newline", "space"],
        help="Heading spacer between log",
    )
    parser.add_argument(
        "--filterout",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="List of filters to filter out",
    )
    parser.add_argument(
        "--keys",
        action="append",
        nargs="*",
        required=False,
        default=None,
        help="Highlight keys",
    )
    parser.add_argument(
        "--highlight",
        nargs="*",
        action="append",
        required=False,
        default=None,
        help="Highlight these phrase",
    )
    parser.add_argument(
        "--h",
        nargs="*",
        action="append",
        required=False,
        default=None,
        help="Highlight these phrase",
    )
    parser.add_argument("--record-dir", type=str, default=None, help="Record Directory")
    parser.add_argument(
        "--record-keys",
        action="append",
        nargs="*",
        required=False,
        default=None,
        help="When recording, only record when these keys change",
    )
    parser.add_argument(
        "--filters",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="List of filters",
    )
    parser.add_argument(
        "--filter-any", action="store_true", help="Filters allow for any of the terms"
    )
    parser.add_argument(
        "--any", action="store_true", help="Filters allow for any of the terms"
    )
    parser.add_argument("--stacktrace", action="store_true", help="Find Stack Traces")
    parser.add_argument(
        "-l",
        "--level",
        action="append",
        choices=list(LOG_LEVEL_CHOICES.keys()),
        default=None,
        type=str,
        help="Only these levels",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="Only these Prefix",
    )
    parser.add_argument(
        "--ignore-prefix",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="Ignore These Prefix",
    )
    parser.add_argument(
        "--ignore-keys",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="Ignore These Keys",
    )
    parser.add_argument(
        "--num-stack-traces",
        help="Default -1 is all. Choose a number for how many stack trace lines to show",
    )


    args = parser.parse_args()

    args.DIVIDER_SIZE = 60

    args.COLOR_STRS = COLOR_STRS
    args.FORE_COLORS = FORE_COLORS
    args.BACK_COLORS = BACK_COLORS
    args.COLOR_RESETTERS = COLOR_RESETTERS
    args.ALL_COLORS = ALL_COLORS

    args.SPACER = " "
    args.DIVIDER = "-" * args.DIVIDER_SIZE
    args.SKIP_UNTIL_REPEAT = 25
    args.MAX_MEMOIZED_MESSAGES = 200
    args.MEMOIZED_MESSAGES = defaultdict(int)
    args.TIME_SEPARATOR = "\n"
    args.HIGHLIGHT_KEYS = []
    args.HIGHLIGHT_PHRASES = []
    args.IGNORE_KEYS = []
    args.PREFIXES = []
    args.IGNORE_PREFIXES = []
    args.LEVELS = []
    args.FILTERS = []
    args.FILTERZ = []
    args.FILTER_OUT = []
    args.PER_LINE = -1
    args.KEY_COUNT = 1
    args.WILL_COUNT = False
    args.TIMING_SECONDS_INTERVAL = None
    args.COUNTED_LOGS = 0
    args.HEADER_SPACER = None
    args.t0 = time.time()
    args.t1 = None
    args.ALLOW_RECORD = True
    args.RECORD_DIR = None
    args.RECORD_KEYS_DIFF = []
    args.PREV_RECORDED_STRING_DICT = {}
    args.FIND_STACKTRACES = False
    args.NUM_STACK_TRACES_TO_PRINT = 6
    args.PREV_MSGS_BEFORE_STACK_TRACE = 6
    args.LEFT_OF_KEY_VALUE = "["
    args.RIGHT_OF_KEY_VALUE = "]"


    if args.spacer == "newline":
        args.spacer  = "\n"
    elif args.spacer == "space":
        args.spacer  = " "
    elif args.spacer == "tab":
        args.spacer  = "\t"
    elif args.spacer == "pipe":
        args.spacer  = " | "
    else:
        pass

    if args.per_line:
        args.PER_LINE = args.per_line
        if SHOW_ARGS:
            print("PER_LINE: {}".format(args.PER_LINE))
    if args.keys:
        args.HIGHLIGHT_KEYS = flatten_list(args.keys)
        if SHOW_ARGS:
            print("HIGHLIGHT_KEYS: {}".format([k for k in args.HIGHLIGHT_KEYS]))
    if args.ignore_keys:
        args.IGNORE_KEYS = flatten_list(args.ignore_keys)
        if SHOW_ARGS:
            print("IGNORE_KEYS: {}".format([k for k in args.IGNORE_KEYS]))
    if args.prefix:
        args.PREFIXES = flatten_list(args.prefix)
        if SHOW_ARGS:
            print("PREFIXES: {}".format([k for k in args.PREFIXES]))
    if args.ignore_prefix:
        args.IGNORE_PREFIXES = flatten_list(args.ignore_prefix)
        if SHOW_ARGS:
            print("IGNORE_PREFIXES: {}".format([k for k in args.IGNORE_PREFIXES]))
    if args.level:
        args.LEVELS = [LOG_LEVEL_CHOICES[l] for l in args.level]
        if SHOW_ARGS:
            print("LEVELS: {}".format([k for k in args.LEVELS]))
    args.FILTERZ = args.filterz if args.filterz else []
    if args.filters or args.FILTERZ:
        args.FILTERS = []
        if args.filters:
            args.FILTERS = flatten_list(args.filters)
        args.FILTERS = args.FILTERS + args.FILTERZ
        args.HIGHLIGHT_PHRASES += args.FILTERS
        if SHOW_ARGS:
            print("FILTERS: {}".format([k for k in args.FILTERS]))
    if args.highlight or args.HIGHLIGHT_PHRASES or args.h:
        args.HIGHLIGHT_PHRASES = (
            flatten_list(args.highlight) if args.highlight else [] + args.HIGHLIGHT_PHRASES
        )
        if args.h:
            args.HIGHLIGHT_PHRASES += flatten_list(args.h)
        if SHOW_ARGS:
            print("HIGHLIGHT_PHRASES: {}".format([k for k in args.HIGHLIGHT_PHRASES]))
    if args.filterout:
        args.FILTER_OUT = flatten_list(args.filterout)
        if SHOW_ARGS:
            print("FILTER_OUT: {}".format([k for k in args.FILTER_OUT]))
    if args.header_spacer == "newline":
        args.HEADER_SPACER = "\n"
    else:
        args.HEADER_SPACER = " " * 4
    if args.time_per_secs > 0:
        args.WILL_COUNT = True
        args.TIMING_SECONDS_INTERVAL = args.time_per_secs
        if SHOW_ARGS:
            print("TIMING NUMBER OF LOGS PER: {} seconds".format(args.TIMING_SECONDS_INTERVAL))
    if args.ALLOW_RECORD:
        if SHOW_ARGS:
            print(
                "Recording enabled. Use {} to trigger record start/stop".format(args.RECORD_KEY)
            )
        if not args.record_dir:
            args.RECORD_DIR = os.getcwd()
        else:
            args.RECORD_DIR = args.record_dir
        if not os.path.exists(args.RECORD_DIR):
            raise ValueError(args.RECORD_DIR + " needs to exist")
        if args.record_keys:
            args.RECORD_KEYS_DIFF = flatten_list(args.record_keys)
            args.HIGHLIGHT_KEYS + args.RECORD_KEYS_DIFF
            if SHOW_ARGS:
                print(
                    "Will record only if the following keys change: {}".format(
                        ",".join(args.RECORD_KEYS_DIFF)
                    )
                )
    if args.stacktrace:
        args.FIND_STACKTRACES = True
        if args.num_stack_traces and args.num_stack_traces > 0:
            args.NUM_STACK_TRACES_TO_PRINT = int(args.num_stack_traces)
        if SHOW_ARGS:
            print("WILL FIND STACK TRACES")
        if SHOW_ARGS:
            print("NUM stack trace lines: {}".format(args.NUM_STACK_TRACES_TO_PRINT))
    if args.flat:
        args.linespace = 0
        args.PER_LINE = -1
        args.divider = False
        args.LEFT_OF_KEY_VALUE = ""
        args.RIGHT_OF_KEY_VALUE = ""
        args.HEADER_SPACER = ""
    return args
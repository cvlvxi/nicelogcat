import argparse
import time
import os
import sys
import json
import jsonargparse
from pathlib import Path
from glob import glob
import nicelogcat.utils as utils
from colorama import Fore
from typing import List
from collections import defaultdict

SHOW_ARGS = False


def ncparser() -> jsonargparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="nicelogcat")
    parser.add_argument(dest="filterz",
                        nargs="*",
                        type=str,
                        help="List of filters")
    parser.add_argument("--title", default="", type=str, help="Title to show")
    parser.add_argument(
        "--suspend-util",
        default=None,
        type=str,
        help="Suspend until this is found",
    )
    parser.add_argument(
        "--spacer",
        default="space",
        choices=["newline", "space", "tab", "pipe"],
        help="spacer to use",
    )
    parser.add_argument(
        "-s",
        "--linespace",
        type=int,
        default=0,
        help="Number of spaces between lines",
    )
    parser.add_argument("--divider",
                        action="store_true",
                        help="Add a divider per line")
    parser.add_argument("--disable", action="store_true", help="Disable Print")
    parser.add_argument("--flat", action="store_true", help="Flat")
    parser.add_argument("--no-flat", action="store_true", help="No Flat")
    parser.add_argument("--raw", action="store_true", help="Include raw line")
    parser.add_argument(
        "--title-line-color",
        default=Fore.BLUE,
        choices=utils.COLOR_STRS,
        help="Color to use if showing title every line",
    )
    parser.add_argument("--per-line",
                        type=int,
                        default=4,
                        help="Keys per line")
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
        "-x",
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
    parser.add_argument("--record-dir",
                        type=str,
                        default=None,
                        help="Record Directory")
    parser.add_argument(
        "--record-keys",
        action="append",
        nargs="*",
        required=False,
        default=None,
        help="When recording, only record when these keys change",
    )
    parser.add_argument(
        "-f",
        "--filters",
        action="append",
        nargs="*",
        default=None,
        type=str,
        help="List of filters",
    )
    parser.add_argument(
        "--filter-any",
        action="store_true",
        help="Filters allow for any of the terms",
    )
    parser.add_argument(
        "-t",
        "--show-title",
        action="store_true",
        help="Show Title",
    )
    parser.add_argument("--align-head",
                        action="store_true",
                        help="Align headers via Prefix / Log LEVEL ")
    parser.add_argument("--no-align-head",
                        action="store_true",
                        help="Disable Align headers via Prefix / Log LEVEL ")
    parser.add_argument("--align-simple",
                        action="store_true",
                        help="Align Use simple alignment method")
    parser.add_argument("--random",
                        action="store_true",
                        help="Random Prefix Foreground Color")
    parser.add_argument("--randomb",
                        action="store_true",
                        help="Random Prefix Background Color")
    parser.add_argument("--random-msg",
                        action="store_true",
                        help="Apply random to msg")
    parser.add_argument("--no-random",
                        action="store_true",
                        help="Disable random colors")
    parser.add_argument("--any",
                        action="store_true",
                        help="Filters allow for any of the terms")
    parser.add_argument("--stacktrace",
                        action="store_true",
                        help="Find Stack Traces")
    parser.add_argument(
        "-l",
        "--level",
        action="append",
        choices=list(utils.LOG_LEVEL_CHOICES.keys()),
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
        "-i",
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
        help="Default -1 is all." +
        "Choose a number for how many stack trace lines to show",
    )
    return parser


def get_args(parser: argparse.ArgumentParser,
             dict_obj: dict = None,
             *args,
             **kwargs) -> argparse.ArgumentParser:
    if args or kwargs or dict_obj:
        if dict_obj:
            list_args = []
            for k, v in dict_obj.items():
                list_args.append(k)
                if not isinstance(v, bool):
                    list_args.append(v)
            args = parser.parse_args(list_args)
        else:
            args = parser.parse_args(*args, **kwargs)
    else:
        args = parser.parse_args()
    args.DIVIDER_SIZE = 60

    args.COLOR_STRS = utils.COLOR_STRS
    args.FORE_COLORS = utils.FORE_COLORS
    args.BACK_COLORS = utils.BACK_COLORS
    args.COLOR_RESETTERS = utils.COLOR_RESETTERS
    args.ALL_COLORS = utils.ALL_COLORS
    args.TITLE = ""
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
    args.HEADER_SPACER = " "
    args.t0 = time.time()
    args.t1 = None
    args.ALLOW_RECORD = True
    args.RECORD_DIR = None
    args.RECORD_KEYS_DIFF = []
    args.PREV_RECORDED_STRING_DICT = {}
    args.FIND_STACKTRACES = False
    args.NUM_STACK_TRACES_TO_PRINT = 10
    args.PREV_MSGS_BEFORE_STACK_TRACE = 4
    args.LEFT_OF_KEY_VALUE = "["
    args.RIGHT_OF_KEY_VALUE = "]"

    return args

def post_process_args(args: dict):

    if args.spacer == "newline":
        args.spacer = "\n"
    elif args.spacer == "space":
        args.spacer = " "
    elif args.spacer == "tab":
        args.spacer = "\t"
    elif args.spacer == "pipe":
        args.spacer = " | "
    else:
        pass
    if args.title:
        args.TITLE = args.title
    if args.per_line:
        args.PER_LINE = args.per_line
        if SHOW_ARGS:
            print("PER_LINE: {}".format(args.PER_LINE))
    if args.keys:
        args.HIGHLIGHT_KEYS = utils.flatten_list(args.keys)
        if SHOW_ARGS:
            print("HIGHLIGHT_KEYS: {}".format([k
                                               for k in args.HIGHLIGHT_KEYS]))
    if args.ignore_keys:
        args.IGNORE_KEYS = utils.flatten_list(args.ignore_keys)
        expanded_items = utils.explode_single_item_list(args.IGNORE_KEYS)
        if expanded_items:
            args.IGNORE_KEYS = expanded_items
        if SHOW_ARGS:
            print("IGNORE_KEYS: {}".format([k for k in args.IGNORE_KEYS]))
    if args.prefix:
        args.PREFIXES = utils.flatten_list(args.prefix)
        if SHOW_ARGS:
            print("PREFIXES: {}".format([k for k in args.PREFIXES]))
    if args.ignore_prefix:
        args.IGNORE_PREFIXES = utils.flatten_list(args.ignore_prefix)
        if SHOW_ARGS:
            print("IGNORE_PREFIXES: {}".format(
                [k for k in args.IGNORE_PREFIXES]))
    if args.level:
        args.LEVELS = [utils.LOG_LEVEL_CHOICES[level] for level in args.level]
        if SHOW_ARGS:
            print("LEVELS: {}".format([k for k in args.LEVELS]))
    args.FILTERZ = args.filterz if args.filterz else []
    if args.filters or args.FILTERZ:
        args.FILTERS = []
        if args.filters:
            args.FILTERS = utils.flatten_list(args.filters)
        args.FILTERS = args.FILTERS + args.FILTERZ
        args.HIGHLIGHT_PHRASES += args.FILTERS
        if SHOW_ARGS:
            print("FILTERS: {}".format([k for k in args.FILTERS]))
    if args.highlight or args.HIGHLIGHT_PHRASES or args.h:
        args.HIGHLIGHT_PHRASES = (utils.flatten_list(
            args.highlight) if args.highlight else [] + args.HIGHLIGHT_PHRASES)
        if args.h:
            args.HIGHLIGHT_PHRASES += utils.flatten_list(
                [x.split(' ') for x in utils.flatten_list(args.h)])
        if SHOW_ARGS:
            print("HIGHLIGHT_PHRASES: {}".format(
                [k for k in args.HIGHLIGHT_PHRASES]))
        args.HIGHLIGHT_PHRASES = list(set(args.HIGHLIGHT_PHRASES))

    if args.filterout:
        args.FILTER_OUT = utils.flatten_list(args.filterout)
        expanded_items = utils.explode_single_item_list(args.FILTER_OUT)
        if expanded_items:
            args.FILTER_OUT = expanded_items
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
            print("TIMING NUMBER OF LOGS PER: {} seconds".format(
                args.TIMING_SECONDS_INTERVAL))
    if args.ALLOW_RECORD:
        if SHOW_ARGS:
            print_str = "Recording enabled"
            print_str += f"Use {args.RECORD_KEY} to trigger record start/stop"
            print(print_str)
        if not args.record_dir:
            args.RECORD_DIR = os.getcwd()
        else:
            args.RECORD_DIR = args.record_dir
        if not os.path.exists(args.RECORD_DIR):
            raise ValueError(args.RECORD_DIR + " needs to exist")
        if args.record_keys:
            args.RECORD_KEYS_DIFF = utils.flatten_list(args.record_keys)
            args.HIGHLIGHT_KEYS + args.RECORD_KEYS_DIFF
            if SHOW_ARGS:
                print(
                    "Will record only if the following keys change: {}".format(
                        ",".join(args.RECORD_KEYS_DIFF)))
    if args.stacktrace:
        args.FIND_STACKTRACES = True
        if args.num_stack_traces and args.num_stack_traces > 0:
            args.NUM_STACK_TRACES_TO_PRINT = int(args.num_stack_traces)
        if SHOW_ARGS:
            print("WILL FIND STACK TRACES")
        if SHOW_ARGS:
            print("NUM stack trace lines: {}".format(
                args.NUM_STACK_TRACES_TO_PRINT))
    if args.flat and not args.no_flat:
        # args.linespace = 0
        args.PER_LINE = -1
        args.divider = False
        args.LEFT_OF_KEY_VALUE = ""
        args.RIGHT_OF_KEY_VALUE = ""
        args.HEADER_SPACER = ""
    return args


def main_args():
    config_dir_arg = '--config-dir'
    no_cfg_args = '--no-cfg'
    check_json_input = ('.json' in sys.argv[-1] or config_dir_arg
                        in sys.argv) and (not no_cfg_args in sys.argv)
    config_dir_idx = -1
    try:
        config_dir_idx = sys.argv.index(config_dir_arg)
    except ValueError:
        pass
    config_dirs = []
    json_args_obj = {}
    base_json_config_dir = Path(__file__).parent.parent / 'configs'
    assert base_json_config_dir.exists()
    config_dirs.append(base_json_config_dir)

    def print_config_help(config_dirs):
        print(f"Maybe you meant one of these?\n\n")
        json_files = []
        for config_dir in config_dirs:
            json_files += [
                x.relative_to(config_dir) for x in config_dir.glob("**/*.json")
            ]
        json_files = sorted(json_files)
        print('\n'.join([str(x) for x in json_files]))
        print('\n')
        sys.exit(1)

    if check_json_input:
        # Check config dir
        custom_config_dir: Path = None
        if config_dir_arg in sys.argv:
            config_dir = sys.argv[config_dir_idx + 1]
            custom_config_dir = Path(config_dir)
            assert custom_config_dir.exists()
            config_dirs.append(custom_config_dir)

        if config_dir_idx != -1 and sys.argv[-1] == str(custom_config_dir):
            print_config_help(config_dirs)

        all_json_files = []
        # Get all json files specified
        if config_dir_idx != -1:
            all_json_files = sys.argv[config_dir_idx + 2:]
        else:
            all_json_files = sys.argv[1:]
        extra_args = None
        extra_args_start_idx = -1
        for idx, i in enumerate(all_json_files):
            if i.startswith('-'):
                extra_args_start_idx = idx
                break;
        if extra_args_start_idx != -1:
            extra_args =  all_json_files[extra_args_start_idx:]
            all_json_files = all_json_files[:extra_args_start_idx]
        all_json_objs = []
        for json_file in all_json_files:
            json_file = Path(json_file)
            if not json_file.exists():
                file_exists = False

                def try_config_dirs(json_file,
                                    config_dirs,
                                    add_suffix: bool = False) -> bool:
                    file_exists = False
                    for config_dir in config_dirs:
                        if add_suffix:
                            new_path = Path(
                                str(config_dir / json_file) + '.json')
                            json_file_in_config_dir = new_path
                        else:
                            json_file_in_config_dir = config_dir / json_file
                        if json_file_in_config_dir.exists():
                            file_exists = True
                            json_file = json_file_in_config_dir
                            break
                    return (file_exists, json_file)

                file_exists, json_file = try_config_dirs(
                    json_file, config_dirs)
                if not file_exists:
                    file_exists, json_file = try_config_dirs(
                        json_file, config_dirs, True)
                if not file_exists:
                    print_config_help(config_dirs)
            json_file = open(json_file, 'r')
            json_obj = {}
            try:
                json_obj = json.load(json_file)
            finally:
                json_file.close
            all_json_objs.append(json_obj)


        def unify_json_objs(all_json_objs: List[dict]) -> dict:
            unified_obj = {}
            for obj in all_json_objs:
                for k, v in obj.items():
                    if k not in unified_obj:
                        unified_obj[k] = v
                    else:
                        if unified_obj[k] == True:
                            continue
                        unified_obj[k] += v
            return unified_obj

        def parse_extra_args(extra_args: List[str]) -> dict:
            if not extra_args:
                return {}
            extra_args_dict = {}
            prev_val = None
            for idx, item in enumerate(extra_args):
                if item != prev_val:
                    if not prev_val:
                        prev_val = item
                        continue
                    if prev_val.startswith('-') and item.startswith('-'):
                        extra_args_dict[prev_val] = True
                    elif prev_val.startswith('-') and not item.startswith('-'):
                        if prev_val in extra_args_dict:
                            extra_args_dict[prev_val] += f",{item}"
                        else:
                            extra_args_dict[prev_val] = item
                    prev_val = item
                if idx == (len(extra_args)-1):
                    if prev_val.startswith('-') and item.startswith('-'):
                        extra_args_dict[item] = True
                    elif prev_val.startswith('-') and not item.startswith('-'):
                        if prev_val in extra_args_dict:
                            extra_args_dict[prev_val] += f",{item}"
                        else:
                            extra_args_dict[prev_val] = item
            for k, v in extra_args_dict.items():
                if ',' in v:
                    extra_args_dict[k] = ' '.join([f"\"{x}\"" for x in v.split(",")])
            return extra_args_dict
        if extra_args:
            all_json_objs.append(parse_extra_args(extra_args))
        json_args_obj = unify_json_objs(all_json_objs)
        parser = ncparser()
        args = get_args(parser, dict_obj=json_args_obj)
        post_process_args(args)
    else:
        if config_dir_idx != -1:
            sys.argv.remove(sys.argv[config_dir_idx+1])
            sys.argv.remove(sys.argv[config_dir_idx])
            sys.argv.remove(sys.argv[sys.argv.index(no_cfg_args)])
        args = get_args(ncparser())
    return (post_process_args(args), json_args_obj)

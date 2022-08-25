from re import I

import argparse
import os
from pathlib import Path

import adblogs._globals as g
from adblogs.adb import adb_clear
from adblogs.utils import a_split
from adblogs.history import write_log_history


def log_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="cool")
    parser.add_argument(
        "-m", "--meta", "--meta-only", dest="meta_only", help="MetaOnly (boxlogs)", action="store_true"
    )
    parser.add_argument(
        "-r", "--raw", dest="raw", help="Add raw line", action="store_true"
    )
    parser.add_argument(
        "-t", "--no-time", dest="no_current_time", help="DisableCurrentTime", action="store_true"
    )
    parser.add_argument(
        "-c", "--clear", dest="adb_clear", help="ClearLogs", action="store_true"
    )
    parser.add_argument("-d", "--debug", help="DebugArgs", action="store_true")
    parser.add_argument(
        "--log-history-dir",
        help="LogHistoryDirectory",
        default=Path(os.path.expanduser("~/.vivi")),
    )
    parser.add_argument(
        "--h",
        "--history",
        dest="show_history",
        help="ShowAndChooseLogHistory",
        action="store_true",
    )
    parser.add_argument(
        "--history-clear",
        "--hc",
        dest="clear_history",
        help="ClearHistoryFile",
        action="store_true",
    )
    parser.add_argument("-i", "--ip", help="IP")
    parser.add_argument(
        "-n",
        "--nf",
        "--no-find",
        dest="no_find",
        help="DisableFind",
        action="store_true",
    )
    parser.add_argument(
        "--fw", 
        "--filter", 
        dest="filter", 
        nargs="*", 
        help="FilterLinesWithWords",
        action="append"
    )
    parser.add_argument(
        "-f", 
        "--find", 
        nargs="*", 
        help="FindTerm", 
        default=g.DEFAULT_FIND,
        action="append",
    )
    parser.add_argument(
        "--fi",
        "--find-ignore",
        dest="find_ignore",
        nargs="*",
        help="IgnoreTermsInFind",
        action="append",
        default=g.DEFAULT_FIND_IGNORE,
    )
    parser.add_argument(
        "--fnd",
        "--find-no-defaults",
        dest="find_no_defaults",
        help="NoDefaultFind",
        action="store_true",
    )
    parser.add_argument(
        "--time-limit",
        "--time",
        "--tl",
        dest="time_limit",
        help="TimeLimitSeconds",
        default=g.DEFAULT_TIME_LIMIT_SECS,
        type=int,
    )
    parser.add_argument(
        "--fp", 
        "--prefixes",
        "--prefix",
        nargs="*", 
        dest="show_prefixes", 
        action="append",
        help="FilterPrefix"
    )
    parser.add_argument(
        "-x",
        dest="find_case_sensitive",
        help="EnableFindCaseSensitive",
        action="store_true",
    )
    parser.add_argument("--fk", nargs="*", dest="show_keys", help="FilterKeys")
    parser.add_argument(
        "--xk",
        "--no-keys",
        nargs="*",
        dest="exclude_keys",
        action="append",
        help="ExcludeKeys",
        default=g.DEFAULT_EXCLUDE_KEYS,
    )
    parser.add_argument(
        "--xv",
        "--no-values",
        nargs="*",
        dest="exclude_values",
        action="append",
        help="ExcludeValues",
        default=g.DEFAULT_EXCLUDE_VALUES,
    )
    parser.add_argument(
        "--xp", 
        "--no-prefixes",
        nargs="*", 
        dest="exclude_prefixes", 
        help="ExcludePrefixes",
        action="append",
        default=g.DEFAULT_EXCLUDE_PREFIXES,
        
    )
    parser.add_argument(
        "--hw",
        nargs="*",
        dest="highlight_words",
        help="HighlightWord",
        default=g.DEFAULT_HIGHLIGHT_WORDS,
        action="append"
    )
    parser.add_argument("--hk", nargs="*", dest="highlight_keys", help="HighlightKey")
    parser.add_argument(
        "--hp", 
        nargs="*", 
        dest="highlight_prefixes", 
        help="HighlightPrefixes",
        action="append"
    )
    args = parser.parse_args()

    args.show_prefixes = a_split(args.show_prefixes)
    args.show_keys = a_split(args.show_keys)
    args.exclude_prefixes = a_split(args.exclude_prefixes)
    args.exclude_keys = a_split(args.exclude_keys)
    args.exclude_values = a_split(args.exclude_values)
    args.highlight_words = a_split(args.highlight_words)
    args.highlight_keys = a_split(args.highlight_keys)
    args.highlight_prefixes = a_split(args.highlight_prefixes)
    args.find = a_split(args.find)

    args.filter = a_split(args.filter)

    if args.filter:
        args.highlight_words += args.filter
    if args.find:
        args.highlight_words += args.find
        if args.find != g.DEFAULT_FIND and not args.find_no_defaults:
            args.find += g.DEFAULT_FIND
            args.highlight_words += g.DEFAULT_FIND
    if args.find_ignore:
        if args.find_ignore != g.DEFAULT_FIND_IGNORE and not args.find_no_defaults:
            args.find_ignore += g.DEFAULT_FIND_IGNORE
    if args.no_find:
        args.find = []
    args.log_history_dir = Path(args.log_history_dir)
    if not args.log_history_dir.exists():
        args.log_history_dir.mkdir()
    args.log_history_file = args.log_history_dir / "adb_log_history"
    write_log_history(parser, args, args.log_history_file)
    if args.adb_clear:
        adb_clear()
    add_defaults(args, 'highlight_words', g.DEFAULT_HIGHLIGHT_WORDS)
    add_defaults(args, 'exclude_keys', g.DEFAULT_EXCLUDE_KEYS)
    add_defaults(args, 'exclude_values', g.DEFAULT_EXCLUDE_VALUES)
    add_defaults(args, 'exclude_prefixes', g.DEFAULT_EXCLUDE_PREFIXES)

    return args


def add_defaults(largs, key, default_val):
    largs_val = largs.__getattribute__(key)
    if largs_val and largs_val != default_val:
        largs_val += default_val
    largs_val = set(list(largs_val))
    largs.__setattr__(key, largs_val)


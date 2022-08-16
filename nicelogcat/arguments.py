
import re
import sys
from argparse import ArgumentParser as _ArgumentParser
from datetime import datetime
from colorama import Fore, Back, Style
from colorama.ansi import AnsiCodes
from collections import Counter
from copy import deepcopy
from dataclasses import Field, dataclass, field, asdict
from dataclasses_json import dataclass_json
from jsonargparse import (
    ArgumentParser,
    ActionParser,
    ActionConfigFile,
    SUPPRESS,
    DefaultHelpFormatter
)
import traceback
from typing import List, TypeVar, Dict, Tuple, Union, Optional

from nicelogcat.utils import (
    r_merge_dicts,
    find_index_in_most_common,
    rand_prefix_colors,
    remove_col_from_val,
    style,
    uplift_flat_dict
)

ArgType = TypeVar("ArgType")


##############################################################
# Argument Dataclasses
##############################################################
@dataclass
class BoolArg:
    flag: str
    dest: str
    help: str = ""
    invert: bool = False

    def add(self, parser: _ArgumentParser):
        args = [self.flag]
        # Assume default off
        kwargs = {'dest': self.dest}
        if self.help:
            kwargs['help'] = self.help
        if not self.invert:
            kwargs['action'] = 'store_true'
            parser.add_argument(*args, **kwargs)


@dataclass
class NonBoolArg:
    flag: str
    dest: str
    is_list: bool = False
    choices: List[str] = None
    default: str = None
    help: str = ""
    required: bool = False

    def add(self, parser: _ArgumentParser):
        args = [self.flag]
        kwargs = {'dest': self.dest}
        if self.is_list:
            kwargs['action'] = 'append'
        if self.default:
            kwargs['default'] = self.default
        else:
            kwargs['default'] = None
        if self.choices:
            kwargs['choices'] = self.choices
        if self.help:
            kwargs['help'] = self.help
        if self.required:
            kwargs['required'] = self.required
        parser.add_argument(*args, **kwargs)


@dataclass
class AlignArgs:
    header_len_counter: Counter = field(default_factory=Counter)
    header_freq_counter: Counter = field(default_factory=Counter)
    header_occurence_check_limit = 5000
    header_most_freq_line = ""
    header_max_len_with_padding = -1
    simple: bool = False
    off: bool = True

    @staticmethod
    def align_header(
        align: "AlignArgs",
        raw_key: str,
        raw_len: int,
        header_str: str
    ) -> str:
        check_limit: int = align.header_occurence_check_limit
        header_len_counter: Counter = align.header_len_counter
        header_freq_counter = align.header_freq_counter
        if not header_len_counter:
            header_len_counter = Counter()
        if not header_freq_counter:
            header_freq_counter = Counter()

        if align.simple:
            if raw_key not in header_len_counter:
                header_len_counter[raw_key] = raw_len
            if not align.header_most_freq_line:
                align.header_most_freq_line = raw_key
            if raw_len > len(align.header_most_freq_line):
                align.header_most_freq_line = raw_key
        else:
            if raw_key not in header_len_counter:
                header_len_counter[raw_key] = raw_len

            if raw_key not in header_len_counter:
                header_freq_counter[raw_key] = 1
            else:
                if raw_key not in header_freq_counter:
                    header_freq_counter[raw_key] = 1
                header_occurences = header_freq_counter[raw_key]
                if header_occurences != check_limit:
                    header_freq_counter[raw_key] += 1

            # Choosing the right header line
            if not align.header_most_freq_line:
                align.header_most_freq_line = raw_key

            # Counters
            biggest_headers = header_len_counter.most_common()
            most_freq_headers = header_freq_counter.most_common()

            # Which index
            curr_size_idx = find_index_in_most_common(biggest_headers, raw_key)
            curr_top_size_idx = find_index_in_most_common(
                biggest_headers, align.header_most_freq_line)
            curr_freq_idx = find_index_in_most_common(most_freq_headers,
                                                      raw_key)
            curr_top_freq_idx = find_index_in_most_common(
                most_freq_headers, align.header_most_freq_line)
            if (curr_size_idx < curr_top_size_idx) and \
               (curr_freq_idx < curr_top_freq_idx):
                align.header_most_freq_line = raw_key

        padding = 10
        most_freq_len = len(align.header_most_freq_line)
        most_freq_len_with_padding = most_freq_len + padding

        if raw_len < most_freq_len_with_padding:
            header_str += " " * (most_freq_len_with_padding - raw_len)
        else:
            diff = raw_len - most_freq_len_with_padding
            header_str += " " * (diff)
        return header_str


@dataclass
class ColorArgs:
    header: AnsiCodes = Back.YELLOW + Fore.BLACK
    log_warn: AnsiCodes = Fore.YELLOW
    log_error: AnsiCodes = Fore.RED
    log_info: AnsiCodes = Fore.GREEN
    time: AnsiCodes = Fore.YELLOW
    current_time: AnsiCodes = Fore.RED
    prefix: AnsiCodes = Fore.GREEN
    title: AnsiCodes = Fore.MAGENTA
    highlight: AnsiCodes = Back.RED + Fore.BLACK,
    highlight_off: AnsiCodes = Back.YELLOW + Fore.BLACK,
    highlight_off_filter: AnsiCodes = Fore.GREEN + Back.BLACK,
    value: AnsiCodes = Fore.WHITE
    key: AnsiCodes = Fore.CYAN
    stacktrace_msg: AnsiCodes = Fore.GREEN,
    path: AnsiCodes = Fore.LIGHTMAGENTA_EX
    timing: AnsiCodes = Back.RED + Fore.BLACK
    change_detected: AnsiCodes = Back.RED + Fore.BLACK

    @staticmethod
    def get_log_level(log_level, color: "ColorArgs"):
        MAX_LOG_WIDTH = 5
        result = [None, None, MAX_LOG_WIDTH]
        if log_level.lower() == "w":
            result[0] = color.log_warn
            result[1] = "WARN"
        elif log_level.lower() == "e":
            result[0] = color.log_error
            result[1] = "ERROR"
        elif log_level.lower() == "d":
            result[0] = color.log_warn
            result[1] = "DEBUG"
        elif log_level.lower() == "i":
            result[0] = color.log_info
            result[1] = "INFO"
        elif log_level.lower() == "v":
            result[0] = color.log_info
            result[1] = "VERBOSE"
        elif log_level.lower() == "f":
            result[0] = color.log_error
            result[1] = "FATAL"
        elif log_level.lower() == "s":
            result[0] = Fore.BLACK
            result[1] = "SILENT"
        else:
            raise ValueError("Unknown log_level found: {}".format(log_level))
        return result


@dataclass
class HighlightArgs:
    phrases: List[str] = field(default_factory=list)
    prefixes: List[str] = field(default_factory=list)
    off: bool = False

    @staticmethod
    def add_argparse_arguments(parser: ArgumentParser) -> List[Union[BoolArg, NonBoolArg]]:
        flags = [
            NonBoolArg("--bleh", "highlight.phrases", is_list=True,
                       help="Highlight these phrases"),
            NonBoolArg('--bleh2', 'highlight.prefixes', is_list=True,
                       help="Highlight these prefixes")
        ]
        for flag in flags:
            flag.add(parser)
        return flags


@dataclass
class FilterArgs:
    include: List[str] = field(default_factory=list)
    include_type: str = "any"
    exclude: List[str] = field(default_factory=list)
    exclude_type: str = "any"
    prefixes: List[str] = field(default_factory=list)
    prefixes_type: str = "any"
    exclude_prefixes: List[str] = field(default_factory=list)
    exclude_prefixes_type: str = "any"
    log_levels: List[str] = field(default_factory=list)
    log_levels_type: str = "any"
    off: bool = False

    @staticmethod
    def add_argparse_arguments(parser: ArgumentParser) -> List[Union[BoolArg, NonBoolArg]]:
        flags = [
            NonBoolArg("-f", "filter.include", is_list=True),
            NonBoolArg('--ftype', 'filter.include_type',
                       choices=["all", "any"], default="any"),
            NonBoolArg("-x", "filter.exclude", is_list=True),
            NonBoolArg('--xtype', 'filter.exclude_type',
                       choices=["all", "any"], default="any"),
            NonBoolArg("-p", "filter.prefixes", is_list=True),
            NonBoolArg('--ptype', 'filter.prefixes_type',
                       choices=["all", "any"], default="any"),
            NonBoolArg("--pi", "filter.exclude_prefixes", is_list=True),
            NonBoolArg('--pitype', 'filter.exclude_prefixes_type',
                       choices=["all", "any"], default="any"),
        ]
        for flag in flags:
            flag.add(parser)
        return flags

    @staticmethod
    def check(
        val,
        check_list: List[str],
        check_type: str,
        casei: bool = True,
        exact: bool = False,
        both_ways: bool = True,
        exclude_empty: bool = True
    ) -> bool:
        if not check_list:
            return True
        if exclude_empty and not val:
            return False
        if casei:
            val = val.lower()
            check_list = [val.lower() for val in check_list]
        check_flag = False
        check_type = any if check_type == "any" else all
        if not exact:
            check_flag = check_type(
                [val in check_val for check_val in check_list])
        else:
            check_flag = check_type(
                [val == check_val for check_val in check_list])
        other_check_flag = False
        if both_ways:
            if not exact:
                check_flag = check_type(
                    [check_val in val for check_val in check_list])
            check_flag = other_check_flag or check_flag
        if 'standalone' in check_list and check_flag:
            print(check_list)
            print(val)
        return check_flag


@dataclass
class LayoutArgs:
    linespace: int = 0
    divider: bool = False
    flat: bool = False
    no_flat: bool = False
    per_line: int = 4
    header_spacer: str = ""
    spacer: str = " "

    @staticmethod
    def add_argparse_arguments(parser: ArgumentParser) -> List[Union[BoolArg, NonBoolArg]]:
        flags = [
            NonBoolArg("-s", "layout.linespace",
                       default=0, help="Spaces between log lines"),
        ]
        for flag in flags:
            flag.add(parser)
        return flags


@dataclass
class LineArgs:
    title: str = "all"
    raw: bool = False
    no_date: bool = False
    no_secs: bool = False
    show_title: bool = False
    align_head: bool = False
    no_align_head: bool = False
    align_simple: bool = False
    left_of_key: str = ""
    right_of_key: str = ""
    off: bool = False
    random_col_background: bool = False
    random_col_message: bool = False
    random_col_off: bool = False


@dataclass
class MetricArgs:
    common_msgs: dict = field(default_factory=dict)
    common_msgs_to_raw: dict = field(default_factory=dict)
    common_msgs_timeframe_secs: int = 120
    counted_logs: int = 0
    off: bool = True


@dataclass
class RecordArgs:
    dir: str = ""
    keys: List[str] = field(default_factory=list)
    key_diff: dict = field(default_factory=dict)
    prev_recorded_string_dict: dict = field(default_factory=dict)
    off: bool = False
    init_recording_state: bool = True
    filename: str = ""
    is_recording: bool = False

    @staticmethod
    def add_argparse_arguments(parser: ArgumentParser) -> List[Union[BoolArg, NonBoolArg]]:
        flags = [
            NonBoolArg("--rd", "record.dir",
                       help="Directory to store recordings", default=""),
            NonBoolArg('--rk', "record.keys",
                       help="Keys to record", is_list=True),
            NonBoolArg("--rf", "record.filename",
                       help="Filename to store recording under", default=""),
        ]
        for flag in flags:
            flag.add(parser)
        return flags


@dataclass
class StacktraceArgs:
    num_stack_traces: int = 10
    prev_lines_before_stacktrace: int = 4
    off: bool = True
    stacktrace_map: dict = field(default_factory=dict)
    stacktrace_colors: dict = field(default_factory=dict)

    @staticmethod
    def add_argparse_arguments(parser: _ArgumentParser):
        flags = [
            NonBoolArg("--num-stacktrace", "stacktrace.num_stack_traces",
                       default=None, help="Num Stacktraces"),
            NonBoolArg("--num-lines-before-stacktrace", "stacktrace.prev_lines_before_stacktrace",
                       default=None, help="Num Lines Before stacktrae"),
            BoolArg('--stacktrace', dest='stacktrace.off',
                    invert=True, help="Enable Stacktrace")
        ]
        for flag in flags:
            flag.add(parser)
        return flags

    @staticmethod
    def find(
        filter: FilterArgs,
        stacktrace: "StacktraceArgs",
        header: str,
        string_dict: Dict[str, str],
        log_time: str,
        is_recording: bool,
        args: "Args"
    ) -> Tuple[str, str]:
        stack_trace_str_no_col = ""
        run_find_stack = True
        prefixes = filter.prefixes
        exclude_prefixes = filter.exclude_prefixes
        stacktrace_map = stacktrace.stacktrace_map
        stacktrace_colors = stacktrace.stacktrace_colors
        if filter.prefixes:
            run_find_stack = header in [p.lower() for p in prefixes]
        if filter.exclude_prefixes:
            run_find_stack = not (header in
                                  [p.lower() for p in exclude_prefixes])
        if run_find_stack:
            stack_trace_str = StacktraceArgs.find_stack(
                stacktrace_map,
                header,
                string_dict,
                stacktrace_colors,
                log_time,
                args=args,
                is_recording=is_recording,
            )
            if stack_trace_str:
                stack_trace_str_no_col = remove_col_from_val(
                    stack_trace_str)
        return stack_trace_str, stack_trace_str_no_col

    @staticmethod
    def find_stack(
        stack_trace_map: dict,
        pfix: str,
        string_dict: dict,
        stack_trace_colors: dict,
        log_time: str,
        args: "Args",
        is_recording: bool,
    ) -> str:
        if not pfix or (args.filter.prefixes and pfix
                        not in args.filter.prefixes):
            return ""
        if pfix not in stack_trace_map:
            stack_trace_map[pfix] = {
                "prefixes": [],
                "stacktraces": [],
                "started": False
            }
            rand_prefix_colors(stack_trace_colors, pfix)
        if "stack" in string_dict:
            stack_msg = string_dict["stack"]
            stack_parts = stack_msg.split("\n", 1)
            stack_prefixes = stack_parts[0]
            stacktraces = stack_parts[1].split("\n")
            return StacktraceArgs.assemble_stack_str(
                log_time=log_time,
                prefix=pfix,
                stack_trace_prefixes=[stack_prefixes],
                stack_trace_lines=stacktraces,
                stack_trace_colors=stack_trace_colors,
                args=args,
                is_recording=is_recording,
            )
        stack_trace_str = ""
        if "message" not in string_dict:
            return ""
        message = string_dict["message"]
        message = message.strip()
        is_a_stack_trace = message.startswith("at ")
        stack_prefixes = stack_trace_map[pfix]["prefixes"]
        stacktraces = stack_trace_map[pfix]["stacktraces"]
        started = stack_trace_map[pfix]["started"]
        if is_a_stack_trace:
            if not started:
                stack_trace_map[pfix]["started"] = True
            stacktraces.append(message)
        else:
            stack_prefixes.append(message)
            if stack_trace_map[pfix]["started"] and len(stacktraces) > 0:
                stack_trace_str = StacktraceArgs.clear_stack(
                    stack_trace_map,
                    pfix,
                    stack_trace_colors,
                    log_time,
                    args=args,
                    is_recording=is_recording,
                )
        if len(stack_prefixes) == args.stacktrace.prev_lines_before_stacktrace:
            stack_trace_map[pfix]["prefixes"] = []
        return stack_trace_str

    @staticmethod
    def assemble_stack_str(
        log_time: str,
        prefix: str,
        stack_trace_prefixes: List[str],
        stack_trace_lines: List[str],
        stack_trace_colors: dict,
        args: "Args",
        is_recording: bool,
    ):

        if args.layout.linespace > 0:
            stack_trace_str = "\n" * args.layout.linespace
        else:
            stack_trace_str = ""

        stack_trace_str += style("-" * 80, color=Fore.BLACK + Back.BLACK)
        stack_trace_str += "\n"
        if not args.record.off and is_recording:
            stack_trace_str += "🟢 "
        if not args.record.off and not is_recording:
            stack_trace_str += "🔴 "

        # Header Line
        curr_time = datetime.now().ctime()
        back_color, fore_color = stack_trace_colors[prefix]
        stack_header_color = back_color + Fore.BLACK
        header_delim = "|"
        stack_trace_str += style(
            f" {prefix.capitalize()} {header_delim} Log Time: {log_time} {header_delim} Current Time: {curr_time}\n", stack_header_color)

        # Stack Prefixes
        stack_trace_str += style("\n".join(
            [x for x in stack_trace_prefixes if x]),
            color=Fore.YELLOW)

        biggest_index = len(stack_trace_lines) - 1
        num_stack_traces = min(args.stacktrace.num_stack_traces, biggest_index)
        continued_str = ""
        if num_stack_traces < biggest_index:
            continued_str = "\n\n(...continued)"

        file_regex = r".*\((.*)\).*"
        tab_space = " " * 4
        for stack_trace in stack_trace_lines[:num_stack_traces]:
            result = re.match(file_regex, stack_trace)
            print_default = False
            if result:
                file_path_str = result.group(1)
                if ":" not in file_path_str:
                    print_default = True
                else:
                    parts = file_path_str.split(":", 1)
                    before_path = stack_trace.split(file_path_str)[0]
                    file_path = parts[0]
                    line_num = parts[1]
                    new_stack_trace = ""
                    new_stack_trace += before_path
                    new_stack_trace += style(file_path, color=Fore.CYAN) + ":"
                    new_stack_trace += style(line_num, color=Fore.YELLOW)
                    stack_trace_str += f"\n{tab_space}{new_stack_trace}"
                    print_default = False

            else:
                print_default = True
            if print_default:
                stack_trace_str += f"\n{tab_space}{stack_trace}"

        # stack_trace_str += "\n\t".join(stack_trace_lines[:num_stack_traces])
        # stack_trace_str += "\n"
        stack_trace_str += continued_str
        # stack_trace_str = stack_trace_str.strip()
        return stack_trace_str

    def clear_stack(
        stack_trace_map: dict,
        pfix: str,
        stack_trace_colors: dict,
        log_time: str,
        args: dict,
        is_recording: bool,
    ):
        stack_trace_str = StacktraceArgs.assemble_stack_str(
            log_time=log_time,
            prefix=pfix,
            stack_trace_prefixes=stack_trace_map[pfix]["prefixes"],
            stack_trace_lines=stack_trace_map[pfix]["stacktraces"],
            stack_trace_colors=stack_trace_colors,
            args=args,
            is_recording=is_recording,
        )
        stack_trace_map[pfix]["started"] = False
        stack_trace_map[pfix]["prefixes"] = []
        stack_trace_map[pfix]["stacktraces"] = []
        return stack_trace_str


##############################################################
# Main argument export
##############################################################
USED_FLAGS = []


class NiceLogCatHelpFormatter(DefaultHelpFormatter):
    @staticmethod
    def is_ignorable_config_action(action) -> bool:
        return ('config' in action.dest) and (not 'config.file' == action.dest)

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = 'Usage: '
        actions = [
            x for x in actions if not self.is_ignorable_config_action(x)]
        return super(NiceLogCatHelpFormatter, self).add_usage(
            usage, actions, groups, prefix)

    def add_argument(self, action):
        if self.is_ignorable_config_action(action):
            return ""
        return super(NiceLogCatHelpFormatter, self).add_argument(action)


@dataclass_json
@dataclass
class Args:
    align: AlignArgs
    color: ColorArgs
    filter: FilterArgs
    highlight: HighlightArgs
    layout: LayoutArgs
    line: LineArgs
    metric: MetricArgs
    record: RecordArgs
    stacktrace: StacktraceArgs

    def debug_print(self, exit: bool = False):
        global USED_FLAGS
        args_copy = deepcopy(self)
        try:
            args_copy.color = None
            args_copy.stacktrace.stacktrace_colors = {}
            args_copy.stacktrace.stacktrace_map = {}
            print()
            print()
            print(style("Settings as config.json:",
                  color=Back.YELLOW + Fore.BLACK))
            print()
            print(style(args_copy.to_json(indent=4), color=Fore.GREEN))
            print()
            print()
            if USED_FLAGS:
                print(style("Shorthand settings:", color=Back.YELLOW + Fore.BLACK))
                print()
                print(
                    style(f"\t{' '.join([flag for flag in USED_FLAGS])}", color=Fore.GREEN))
                print()
        except Exception as e:
            print(str(e))
        pass
        if exit:
            sys.exit(1)


class ExtraArgs:
    ip: Optional[str] = None
    from_log: Optional[str] = None

    def find_arg_in_argv(self, field: str, flags: List[str] | str):
        if isinstance(flags, str):
            flags = [flags]
        final_val = None
        vals = []
        for flag in flags:
            if flag in sys.argv:
                try:
                    flag_idx = sys.argv.index(flag)
                    for item in sys.argv[flag_idx+1:]:
                        if item.startswith('-'):
                            break
                        vals.append(item)
                    sys.argv.remove(flag)
                    final_val = " ".join(vals)
                    for val in vals:
                        sys.argv.remove(val)
                except Exception as e:
                    print(traceback.format_exc())
                    pass 
        if final_val:
            self.__setattr__(field, final_val)

class NiceLogCatArgs:

    @staticmethod
    def cfg_parser(with_cfg: bool = False) -> ArgumentParser:
        parser = ArgumentParser(
            add_help=True, formatter_class=NiceLogCatHelpFormatter)

        parser.add_dataclass_arguments(
            AlignArgs, nested_key="align", default=AlignArgs())
        parser.add_dataclass_arguments(
            FilterArgs, nested_key="filter", default=FilterArgs())
        parser.add_dataclass_arguments(
            HighlightArgs, nested_key="highlight", default=HighlightArgs())
        parser.add_dataclass_arguments(
            LayoutArgs, nested_key="layout", default=LayoutArgs())
        parser.add_dataclass_arguments(
            LineArgs, nested_key="line", default=LineArgs())
        parser.add_dataclass_arguments(
            RecordArgs, nested_key="record", default=RecordArgs())
        parser.add_dataclass_arguments(
            StacktraceArgs, nested_key="stacktrace", default=StacktraceArgs())
        if with_cfg:
            parser.add_argument('--file', action=ActionConfigFile)
        return parser

    @staticmethod
    def custom_parser() -> _ArgumentParser:
        parser = _ArgumentParser(
            add_help=True, exit_on_error=False)
        return parser

    @staticmethod
    def pop_from_sys_argv(flags: List[Union[BoolArg, NonBoolArg]]):
        global USED_FLAGS
        popped_val = None
        popped_key = None
        for flag in flags:
            while flag.flag in sys.argv:
                try:
                    flag_idx = sys.argv.index(flag.flag)
                    if isinstance(flag, NonBoolArg):
                        flag_val_idx = flag_idx + 1
                        popped_val = sys.argv.pop(flag_val_idx)
                    popped_key = sys.argv.pop(flag_idx)
                    if popped_key:
                        USED_FLAGS.append(popped_key)
                    if popped_val:
                        USED_FLAGS.append(popped_val)
                except:
                    pass

    @staticmethod
    def get_arguments() -> Tuple[Args, Optional[str]]:
        print(sys.argv)
        flags = []
        extra_args = ExtraArgs()
        extra_args.find_arg_in_argv("ip", "--ip")
        extra_args.find_arg_in_argv("from_log", "--from")

        # Custom Parser for shorthand
        custom_parser = NiceLogCatArgs.custom_parser()
        # Add flags to pop
        flags += FilterArgs.add_argparse_arguments(custom_parser)
        flags += StacktraceArgs.add_argparse_arguments(custom_parser)
        flags += HighlightArgs.add_argparse_arguments(custom_parser)
        flags += LayoutArgs.add_argparse_arguments(custom_parser)
        flags += RecordArgs.add_argparse_arguments(custom_parser)
        custom_args, _ = custom_parser.parse_known_args()
        custom_args_dict = uplift_flat_dict(custom_args.__dict__)
        NiceLogCatArgs.pop_from_sys_argv(flags)

        # Cfg Parser + Json Parser for cli
        cliparser: ArgumentParser = NiceLogCatArgs.cfg_parser()
        configparser: ArgumentParser = NiceLogCatArgs.cfg_parser(with_cfg=True)
        action_configparser = ActionParser(configparser)
        cliparser.add_argument("--config",
                               action=action_configparser,
                               help=SUPPRESS)
        joined_parser = cliparser.parse_args()
        cli_args: dict = joined_parser.as_dict()
        config_args: dict = cli_args.pop("config")
        if "file" in config_args:
            config_args.pop("file")
        if "__path__" in config_args:
            config_args.pop("__path__")

        main_args: dict = r_merge_dicts(config_args, cli_args)
        main_args: dict = r_merge_dicts(
            main_args, custom_args_dict, smaller_r=True)

        args_field_dict = Args.__dataclass_fields__
        for arg_type, value in main_args.items():
            arg_field = args_field_dict[arg_type]
            cls_type: Field = arg_field.type
            main_args[arg_type] = cls_type(**value)

        missing_args = {
            arg_type: args_field
            for arg_type, args_field in args_field_dict.items()
            if arg_type not in main_args
        }
        for arg_type, arg_field in missing_args.items():
            arg_field: Field
            cls_type = arg_field.type
            main_args[arg_type] = cls_type()
        main_args: Args = Args(**main_args)
        return main_args, extra_args

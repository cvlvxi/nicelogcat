from ast import Tuple
import re
from colorama import Fore, Back
from colorama.ansi import AnsiCodes
from collections import Counter
from dataclasses import Field, dataclass, field
from enum import Enum
from jsonargparse import (
    ArgumentParser,
    ActionParser,
    ActionConfigFile,
    SUPPRESS
)
from typing import List, TypeVar, Dict, Tuple

from nicelogcat.utils import (
    r_merge_dicts,
    find_index_in_most_common,
    rand_prefix_colors,
    remove_col_from_val,
    style
)

ArgType = TypeVar("ArgType")


class FilterType(Enum):
    all = "all"
    any = "any"


##############################################################
# Argument Dataclasses
##############################################################
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
    highlight_off: AnsiCodes = Fore.BLACK + Back.YELLOW
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


@dataclass
class FilterArgs:
    include: List[str] = field(default_factory=list)
    include_type: FilterType = FilterType.all
    exclude: List[str] = field(default_factory=list)
    exclude_type: FilterType = FilterType.any
    prefixes: List[str] = field(default_factory=list)
    prefixes_type: FilterType = FilterType.any
    exclude_prefixes: List[str] = field(default_factory=list)
    exclude_prefixes_type: FilterType = FilterType.any
    log_levels: List[str] = field(default_factory=list)
    log_levels_type: FilterType = FilterType.any
    off: bool = False

    @staticmethod
    def check(
        val,
        check_list: List[str],
        check_type: FilterType,
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
        check_type = any if FilterType.any else all
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


@dataclass
class StacktraceArgs:
    num_stack_traces: int = 10
    prev_lines_before_stacktrace: int = 4
    off: bool = True
    stacktrace_map: dict = field(default_factory=dict)
    stacktrace_colors: dict = field(default_factory=dict)

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
        back_color, fore_color = stack_trace_colors[prefix]
        # stack_trace_str += style(f"{prefix}Exception", fore_color)
        stack_trace_str += style(f" {prefix}", fore_color)
        # stack_trace_str += style(" " * 5, back_color + Fore.BLACK)
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
def arg_options(no_help: bool = False, **kwargs: dict) -> dict:
    _args = {}
    if "no_help" in kwargs:
        no_help = kwargs.pop()
    _args |= kwargs
    if no_help:
        _args["help"] = SUPPRESS
    return _args


@dataclass
class NiceLogCatArgs:

    @staticmethod
    def cfg_parser(with_cfg: bool = False,
                   no_help: bool = False) -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_dataclass_arguments(
            AlignArgs,
            **(arg_options(nested_key="align",
                           default=AlignArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            FilterArgs,
            **(arg_options(nested_key="filter",
                           default=FilterArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            HighlightArgs,
            **(arg_options(nested_key="highlight",
                           default=HighlightArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            LayoutArgs,
            **(arg_options(nested_key="layout",
                           default=LayoutArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            LineArgs,
            **(arg_options(nested_key="line", default=LineArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            RecordArgs,
            **(arg_options(nested_key="record",
                           default=RecordArgs(),
                           no_help=no_help)))
        parser.add_dataclass_arguments(
            StacktraceArgs,
            **(arg_options(nested_key="stacktrace",
                           default=StacktraceArgs(),
                           no_help=no_help)))
        if with_cfg:
            parser.add_argument('--load', action=ActionConfigFile)
        return parser


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


def get_arguments():
    cliparser: ArgumentParser = NiceLogCatArgs.cfg_parser()
    configparser: ArgumentParser = NiceLogCatArgs.cfg_parser(with_cfg=True,
                                                             no_help=True)
    action_configparser = ActionParser(configparser)
    cliparser.add_argument("--config",
                           action=action_configparser,
                           help=SUPPRESS)
    joined_parser = cliparser.parse_args()

    cli_args: dict = joined_parser.as_dict()
    config_args: dict = cli_args.pop("config")

    if "load" in config_args:
        config_args.pop("load")
    if "__path__" in config_args:
        config_args.pop("__path__")

    main_args: dict = r_merge_dicts(config_args, cli_args)
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
    main_args = Args(**main_args)
    return main_args

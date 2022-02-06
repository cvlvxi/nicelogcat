import os
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from colorama import init, Fore, Back
from colorama.ansi import AnsiCodes
from pynput import keyboard
from traceback import print_exc
from typing import Tuple, Optional, BinaryIO


from nicelogcat.arguments import (
    AlignArgs,
    Args,
    ColorArgs,
    FilterArgs,
    StacktraceArgs
)

import nicelogcat.utils as utils

init(autoreset=True)

########################################################
# Globals
########################################################
_args: Args = None
IS_RECORDING: bool = False
INIT_NOT_RECORDING_STATE: bool = False
TITLE = "all"
RECORD_DIR = os.curdir

KEY_RECORD = keyboard.Key.f12
KEY_SHOW_ARGS = keyboard.Key.f11


def show_available_keys():
    print(utils.style("Available keys:", Fore.GREEN))
    print(utils.style(f"\tShow Configuration Key: f11", Fore.YELLOW))
    print(utils.style(f"\tRecord Key: f12", Fore.YELLOW))


show_available_keys()


def on_press(key):
    global IS_RECORDING
    global INIT_NOT_RECORDING_STATE
    global RECORD_FILE_NAME
    global TITLE
    global RECORD_DIR
    global _args
    global _console
    set_filename = False
    try:
        if key == KEY_RECORD:
            IS_RECORDING = not IS_RECORDING
            INIT_NOT_RECORDING_STATE = False
            if not INIT_NOT_RECORDING_STATE and IS_RECORDING:
                if not TITLE:
                    TITLE = "logcat"
                set_filename = True
            if not INIT_NOT_RECORDING_STATE and not IS_RECORDING:
                set_filename = True
            if set_filename:
                if TITLE not in os.listdir(RECORD_DIR):
                    RECORD_FILE_NAME = TITLE + "_0.log"
                else:
                    curr_files = [
                        int(x.rsplit(".log")[0].rsplit("_")[-1])
                        for x in os.listdir(RECORD_DIR) if TITLE in x
                    ]
                    curr_files = sorted(curr_files)
                    next_inc = 0
                    if curr_files:
                        next_inc = int(curr_files[-1]) + 1
                    RECORD_FILE_NAME = TITLE + "_{}.log".format(next_inc)
        elif key == KEY_SHOW_ARGS:
            try:
                args_copy = deepcopy(_args)
                args_copy.color = None
                args_copy.stacktrace.stacktrace_colors = {}
                args_copy.stacktrace.stacktrace_map = {}
                print()
                print()
                print(utils.style("Settings as config.json:", color=Back.YELLOW + Fore.BLACK))
                print()
                print(utils.style(args_copy.to_json(indent=4), color=Fore.GREEN))
            except Exception as e:
                print(str(e))
            pass

    except AttributeError:
        pass


########################################################
# Dataclasses
########################################################


@dataclass
class ValueColor:
    value: str
    color: any


@dataclass
class Output:
    header_output: str
    output: str
    change_detected: bool
    stacktrace: str

    @staticmethod
    def default() -> "Output":
        return Output("", "", False, "")


@dataclass
class Headers:
    prefix: ValueColor
    log_level: ValueColor
    log_time: ValueColor

    def length(self, delimiter: str = " ", raw: bool = False) -> int:
        return len(self.to_string(delimiter=delimiter, raw=raw))

    def prefix_only_string(
        self,
        delimiter: str = " ",
    ) -> str:
        return (delimiter * len(self.log_time.value)) + delimiter + \
               (delimiter * len(self.log_level.value)) + delimiter + \
            self.prefix.value

    def to_string(self, delimiter: str = " ", raw: bool = False) -> str:
        return delimiter.join([
            self.log_time.value if raw else utils.style(
                self.log_time.value, self.log_time.color),
            self.log_level.value if raw else utils.style(
                self.log_level.value, self.log_level.color),
            self.prefix.value
            if raw else utils.style(self.prefix.value, self.prefix.color),
        ])

    @property
    def keys(self):
        return ["log_time", "level", "prefix"]


########################################################
# Main Loop
########################################################

async def main_loop(args: Args, stream: BinaryIO) -> Output:
    global _args
    global IS_RECORDING
    global TITLE
    global RECORD_DIR
    global RECORD_FILE_NAME
    _args = args
    TITLE = _args.line.title.lower().replace(" ", "_") \
        if _args.line.title else ""
    RECORD_DIR = _args.record.dir if os.path.exists(
        _args.record.dir) else os.curdir

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

            # Find loglevel index
            levels = [
                level for level in utils.LOG_LEVEL_CHOICES.keys()
                if len(level) == 1
            ]
            log_level_idx = [
                idx for idx, val in enumerate(parts)
                if len(val.strip()) == 1 and val.strip().lower() in levels
            ]
            if not log_level_idx:
                continue
            log_level_idx = log_level_idx[0]
            (log_level_color, log_level, max_log_width) = \
                ColorArgs.get_log_level(
                utils.norm_str3(parts[log_level_idx]), _args.color)
            if len(log_level) < max_log_width:
                log_level += " " * (max_log_width - len(log_level))

            prefix = utils.norm_str3(parts[log_level_idx + 1]).strip()
            msg = utils.norm_str3(" ".join(parts[log_level_idx + 2:]))
            if _args.line.no_secs:
                timestamp = timestamp.rsplit(".", 1)[0]
            if _args.line.no_date:
                log_time = f"{timestamp}"
            else:
                log_time = f"[{date}] {timestamp}"
            headers = Headers(
                prefix=ValueColor(value=prefix,
                                  color=_args.color.prefix),
                log_level=ValueColor(value=log_level, color=log_level_color),
                log_time=ValueColor(value=log_time,
                                    color=_args.color.time))

            output: Output = nice_print(
                _args,
                headers,
                utils.nested_dicts({"message": msg}),
                rawline=line,
                force_disable_print=_args.line.off,
                is_recording=IS_RECORDING
            )
            if output == Output.default():
                continue
            if _args.line.off:
                output.output = ""

            if not _args.record.off and IS_RECORDING:
                record_file_path = os.path.join(RECORD_DIR,
                                                RECORD_FILE_NAME)
                write_to_file = True
                if _args.record.key_diff:
                    write_to_file = output.change_detected
                with open(record_file_path, "a") as f:
                    if write_to_file:
                        if output.output:
                            f.write(f"{headers.to_string()} {output.output}")
                        if output.stacktrace:
                            f.write(f"{output.stacktrace}")
            yield output

    except StopIteration:
        pass
    except KeyboardInterrupt:
        import sys

        sys.exit(1)
    except Exception:
        print_exc()


def nice_print(
    args: Args,
    headers: Headers,
    message_dict: dict,
    rawline: str,
    force_disable_print: bool,
    is_recording: bool,
) -> Tuple[Optional[str], bool]:
    h: Headers = headers
    nested_spacer = " "
    top_spacer = " "
    readable_time = ""

    readable_time = None

    def get_date(t, strf, readable_time) -> datetime:
        try:
            readable_time = datetime.strptime(t, strf)
        except:
            pass
        return readable_time

    date_strfs = ["[%m-%d] %H:%M:%S.%f",
                  "[%Y-%m-%d] %H:%M:%S.%f",
                  "[%m-%d] %H:%M:%S",
                  "%H:%M:%S"]

    for strf in date_strfs:
        readable_time = get_date(h.log_time.value, strf, readable_time)
        if readable_time:
            break
    log_time = ""
    if readable_time:
        new_datetime = datetime(
            year=datetime.now().year,
            month=readable_time.day or 0,
            day=readable_time.day or 0,
            hour=readable_time.hour or 0,
            minute=readable_time.minute or 0,
            second=readable_time.second or 0)
        log_time = new_datetime.ctime()

    key_color = args.color.key
    value_color = args.color.value

    if not args.line.random_col_off:
        stacktrace_colors = args.stacktrace.stacktrace_colors
        stacktrace_colors = utils.rand_prefix_colors(stacktrace_colors,
                                                     h.prefix.value,
                                                     ignore_col=key_color)
        prefix_col = stacktrace_colors[h.prefix.value]
        if args.line.random_col_background:
            chosen_col = prefix_col[0] + Fore.BLACK
        else:
            chosen_col = prefix_col[1]
        headers.prefix.color = chosen_col
        if args.line.random_col_message:
            value_color = chosen_col

    if not args.filter.off:
        has_log: bool = FilterArgs.check(h.log_level.value,
                                         args.filter.log_levels,
                                         args.filter.log_levels_type)
        if not has_log:
            return Output.default()

        has_prefix = FilterArgs.check(h.prefix.value.strip(),
                                      args.filter.prefixes,
                                      args.filter.prefixes_type,
                                      both_ways=True)
        if not has_prefix:
            return Output.default()

        has_ignored_prefix = False
        if args.filter.exclude_prefixes:
            has_ignored_prefix = FilterArgs.check(
                h.prefix.value.strip(),
                args.filter.exclude_prefixes,
                args.filter.exclude_prefixes_type,
                both_ways=True)

        if has_ignored_prefix:
            return Output.default()

    header_line_str = headers.to_string()
    header_line_raw_str = headers.to_string(raw=True)
    raw_len = len(header_line_raw_str)

    raw_key = headers.prefix_only_string(delimiter="x")
    if not args.align.off:
        header_line_str = AlignArgs.align_header(args.align,
                                                 raw_key,
                                                 raw_len,
                                                 header_line_str)

    header_line_str += args.layout.header_spacer

    string_list = []
    key_order = []
    meta_keys = []

    for k, v in message_dict.items():
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
        v = message_dict[key]
        if not v:
            continue
        if not k:
            continue
        if k in headers.keys:
            continue
        k = utils.norm_str(k)
        non_color_k = k
        k = utils.style(k, color=key_color)

        if isinstance(v, dict):
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                top_spacer,
                v,
                key_color=key_color,
                value_color=value_color,
                args=args,
            )
            key_count = new_key_count
            string_list.append("{}:{}{}".format(
                k,
                nested_spacer,
                nice_str,
            ))
            nested_d = utils.find_dict_in_v(v, rawline)
            if nested_d:
                string_dict.update(utils.flatten_dict(nested_d))
            else:
                string_dict[non_color_k] = v
        else:
            nested_d = utils.find_dict_in_v(v, rawline)
            (new_key_count, nice_str) = nice_print_dict(
                key_count,
                top_spacer,
                nested_d,
                key_color=key_color,
                value_color=value_color,
                args=args,
            )
            key_count = new_key_count
            if nested_d:
                if nice_str:
                    string_list.append(nice_str)
                string_dict.update(utils.flatten_dict(nested_d))

            else:
                string_dict[non_color_k] = v
                string_list.append("{}{}: {}{}".format(
                    args.line.left_of_key,
                    k,
                    utils.style(v, color=value_color),
                    args.line.right_of_key
                ))

    if args.line.raw:
        string_list.append("[{}: {}]".format(
            utils.style("rawline", color=key_color),
            utils.style(rawline, color=value_color)
        ))

    stack_trace_str = ""
    stack_trace_str_no_col = ""

    if not args.stacktrace.off:
        stack_trace_str, stack_trace_str_no_col = \
            StacktraceArgs.find(
                args.filter,
                args.stacktrace,
                headers.prefix.value.lower(),
                string_dict,
                log_time,
                is_recording,
                args)
    will_print = True
    result_str = args.layout.spacer.join([x for x in string_list if x])
    result_str_no_col = utils.remove_col_from_val(result_str)

    string_dict = utils.flatten_dict(string_dict)

    changed_keys = []
    change_detected = False
    if force_disable_print or args.line.off:
        will_print = False

    if not args.record.off and args.record.key_diff:
        prev_recorded_string_dict = args.record.prev_recorded_string_dict
        for key in args.record.key.diff:
            if (key in string_dict
                    and key not in prev_recorded_string_dict):
                prev_recorded_string_dict[key] = string_dict[key]
            if (key in string_dict and
                    string_dict[key] != prev_recorded_string_dict[key]):
                changed_keys.append(key)
                change_detected = True
        # Highlight keys
        for key in changed_keys:
            result_str = result_str.replace(
                key,
                utils.style(key, color=args.color.change_detected)
            )
        # Update
        for key in string_dict:
            prev_recorded_string_dict[key] = string_dict[key]
        if args.record.key_diff and not change_detected:
            will_print = False
            return ("", False)

    if not args.highlight.off:
        for phrase in set(args.highlight.phrases):
            if phrase.lower() in result_str.lower():
                start_idx = result_str.lower().find(phrase.lower())
                end_index = start_idx + len(phrase)
                first_section = utils.style(
                    result_str[0:start_idx],
                    color=args.color.highlight_off
                    if not args.filter.include else "")
                middle_section = utils.style(
                    result_str[start_idx:end_index],
                    color=args.color.highlight)
                end_section = utils.style(
                    result_str[end_index:],
                    color=args.color.highlight_off
                    if not args.filter.include else "")
                result_str = first_section + middle_section + end_section

    if not args.filter.off:
        if args.filter.include:
            will_print = FilterArgs.check(result_str_no_col,
                                          args.filter.include,
                                          args.filter.include_type)
            if stack_trace_str:
                will_print = FilterArgs.check(stack_trace_str_no_col,
                                              args.filter.include,
                                              args.filter.include_type)
        if args.filter.exclude:
            will_print = not FilterArgs.check(result_str_no_col,
                                              args.filter.exclude,
                                              args.filter.exclude_type)
            if stack_trace_str:
                will_print = not FilterArgs.check(stack_trace_str_no_col,
                                                  args.filter.exclude,
                                                  args.filter.exclude_type)

    divider_str = args.layout.divider + "\n" if args.layout.divider else ""

    if not args.record.off:
        if is_recording:
            header_line_str = "🟢" + " " + header_line_str
        else:
            header_line_str = "🔴" + " " + header_line_str

    header_output = divider_str
    header_output += header_line_str
    header_output += top_spacer
    header_output += args.layout.spacer
    thing_to_print = result_str.strip()
    if args.layout.linespace > 0:
        thing_to_print = thing_to_print + '\n' * args.linespace
    if will_print:
        return Output(header_output=header_output,
                      output=thing_to_print,
                      change_detected=change_detected,
                      stacktrace=stack_trace_str)
    else:
        return Output(header_output="",
                      output="",
                      change_detected=False,
                      stacktrace=stack_trace_str)


def nice_print_dict(
    key_count: int,
    top_spacer: str,
    some_dict: dict,
    key_color: AnsiCodes,
    value_color: AnsiCodes,
    args: Args
) -> Tuple[int, str]:
    nice_str = ""
    nice_strings = []

    spacer = args.layout.spacer
    for k, v in some_dict.items():
        if isinstance(v, dict):
            (new_key_count,
             nice_str) = nice_print_dict(key_count, top_spacer, v, key_color,
                                         value_color, args)

            nice_strings.append(nice_str)
            key_count = new_key_count
        else:
            if args.filter.exclude:
                ignore_k = FilterArgs.check(
                    k,
                    args.filter.exclude,
                    args.filter.exclude_prefixes_type)
                if ignore_k:
                    continue
            nice_strings.append(spacer + "{}{}: {}{}".format(
                args.line.left_of_key,
                utils.style(str(k).strip(), color=key_color),
                utils.style(str(v).strip(), color=value_color),
                args.line.right_of_key
            ))
            key_count += 1
    if nice_strings:
        nice_str = spacer.join([x for x in nice_strings if x])
    return (key_count, nice_str)

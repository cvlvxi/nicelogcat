import time
import os
import sys
import json
import nicelogcat.utils as utils
from box import Box
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from colorama import init, Fore
from pynput import keyboard
from traceback import print_exc
from typing import Tuple, Optional, BinaryIO, List

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
HEADER_LEN_COUNTER = Counter()
HEADER_FREQ_COUNTER = Counter()
HEADER_OCCURENCE_CHECK_LIMIT = 5000
MOST_FREQ_HEADER_LINE = ""
MAX_LEN_HEADER_WITH_PADDING = ""
COMMON_MSGS = defaultdict(dict)
COMMON_MSGS_TO_RAWLINE = {}
COMMON_MSG_TIMEFRAME_SECS = 120
JSON_ARGS_OBJ = None


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


async def main_loop(args: Box,
                    stream: BinaryIO,
                    json_args_obj: dict = None) -> Output:
    global TITLE
    global RECORD_DIR
    global COMMON_MSGS
    global COMMON_MSGS_TO_RAWLINE
    global JSON_ARGS_OBJ
    if json_args_obj:
        JSON_ARGS_OBJ = json_args_obj
    RECORD_DIR = args.record_dir
    TITLE = args.title.lower().replace(" ", "_") if args.title else ""
    common_t0 = time.time()
    try:
        while True:
            common_t1 = time.time()
            if (common_t1 - common_t0) >= COMMON_MSG_TIMEFRAME_SECS:
                common_t0 = time.time()
                COMMON_MSGS = defaultdict(dict)
                COMMON_MSGS_TO_RAWLINE = {}
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
            levels = [level for level in utils.LOG_LEVEL_CHOICES.keys() if len(level) == 1]
            log_level_idx = [idx for idx, val in enumerate(parts) if len(val.strip()) == 1 and val.strip().lower() in levels]
            if not log_level_idx:
                continue
            log_level_idx = log_level_idx[0]
            (log_level_color, log_level,
             max_log_width) = utils.get_log_level(utils.norm_str3(parts[log_level_idx]),
                                                  args.colors)
            if len(log_level) < max_log_width:
                log_level += " " * (max_log_width - len(log_level))

            prefix = utils.norm_str3(parts[log_level_idx+1]).strip()
            msg = utils.norm_str3(" ".join(parts[log_level_idx+2:]))
            print(args.no_secs)
            import sys
            sys.exit(1)
            if args.no_secs:
                timestamp = timestamp.rsplit(".", 1)[0]
            if args.no_date:
                log_time = f"{timestamp}"
            else:
                log_time = f"[{date}] {timestamp}"
            headers = Headers(
                prefix=ValueColor(value=prefix,
                                  color=args.colors["PREFIX_COLOR"]),
                log_level=ValueColor(value=log_level, color=log_level_color),
                log_time=ValueColor(value=log_time,
                                    color=args.colors["TIME_COLOR"]))
            output: Output = nice_print(
                args,
                headers,
                utils.nested_dicts({"message": msg}),
                rawline=line,
                force_disable_print=FORCE_DISABLE_PRINT,
                is_recording=IS_RECORDING,
            )
            if output == Output.default():
                continue
            if FORCE_DISABLE_PRINT or args.disable:
                output.output = ""
            # Record common_msgs
            if output.output not in COMMON_MSGS[headers.prefix.value]:
                COMMON_MSGS[headers.prefix.value] = Counter()
                COMMON_MSGS_TO_RAWLINE[headers.prefix.value] = defaultdict(str)
            COMMON_MSGS[headers.prefix.value][output.output] += 1
            COMMON_MSGS_TO_RAWLINE[output.output] = line.strip()
            if args.ALLOW_RECORD and IS_RECORDING:
                record_file_path = os.path.join(args.RECORD_DIR,
                                                RECORD_FILE_NAME)
                write_to_file = True
                if args.RECORD_KEYS_DIFF:
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
    args: dict,
    headers: Headers,
    message_dict: dict,
    rawline: str,
    force_disable_print: bool,
    is_recording: bool,
) -> Tuple[Optional[str], bool]:
    global HEADER_SPACER
    global COUNTED_LOGS
    global PREV_RECORDED_STRING_DICT
    global STACK_TRACE_COLORS
    global STACK_TRACE_MAP
    global HEADER_LEN_COUNTER
    global HEADER_FREQ_COUNTER
    global HEADER_OCCURENCE_CHECK_LIMIT
    global MOST_FREQ_HEADER_LINE

    h: Headers = headers
    header_pure_val = [h.prefix.value, h.log_level.value, h.log_time.value]
    header_len = len(" ".join(header_pure_val))
    header_space_max = 33
    header_diff = header_space_max - header_len

    total_header_len = header_len + header_diff
    nested_spacer = " "
    top_spacer = ("\n{}{}".format(args.HEADER_SPACER, " " *
                                  total_header_len) if
                  (not args.flat or args.no_flat) else " ")
    readable_time = ""
    try:
        readable_time: datetime = datetime.strptime(h.log_time.value,
                                                    "[%m-%d] %H:%M:%S.%f")
    except Exception:
        readable_time: datetime = datetime.strptime(h.log_time.value,
                                                    "[%Y-%m-%d] %H:%M:%S.%f")

    # Assume current year?
    new_datetime = datetime(
        year=datetime.now().year,
        month=readable_time.month,
        day=readable_time.day,
        hour=readable_time.hour,
        minute=readable_time.minute,
        second=readable_time.second,
    )
    log_time = new_datetime.ctime()
    value_col = args.colors["V_COLOR"]
    if (args.random or args.randomb) and not (args.no_random):
        utils.rand_prefix_colors(STACK_TRACE_COLORS,
                                 h.prefix.value,
                                 ignore_col=args.colors["K_COLOR"])
        prefix_col = STACK_TRACE_COLORS[h.prefix.value]
        if args.random:
            chosen_col = prefix_col[1]
        elif args.randomb:
            chosen_col = prefix_col[0] + Fore.BLACK
        headers.prefix.color = chosen_col
        if args.random_msg:
            value_col = chosen_col

    if args.level and any([h.log_level.value not in x for x in args.LEVELS]):
        return Output.default()

    prefix_exists_check = [
        h.prefix.value.strip().lower() != x.lower() for x in args.PREFIXES
    ]

    if args.PREFIXES and all(prefix_exists_check) or not h.prefix.value:
        return Output.default()

    ignore_prefix_check = [h.prefix.value in x for x in args.IGNORE_PREFIXES]

    if args.ignore_prefix and any(ignore_prefix_check):
        return Output.default()

    header_line_str = headers.to_string()
    header_line_raw_str = headers.to_string(raw=True)
    raw_len = len(header_line_raw_str)
    raw_key = headers.prefix_only_string(delimiter="x")

    if args.align_head and not args.no_align_head:
        if args.align_simple:
            if raw_key not in HEADER_LEN_COUNTER:
                HEADER_LEN_COUNTER[raw_key] = raw_len
            if not MOST_FREQ_HEADER_LINE:
                MOST_FREQ_HEADER_LINE = raw_key
            if raw_len > len(MOST_FREQ_HEADER_LINE):
                MOST_FREQ_HEADER_LINE = raw_key
        else:
            if raw_key not in HEADER_LEN_COUNTER:
                HEADER_LEN_COUNTER[raw_key] = raw_len

            if raw_key not in HEADER_LEN_COUNTER:
                HEADER_FREQ_COUNTER[raw_key] = 1
            else:
                header_occurences = HEADER_FREQ_COUNTER[raw_key]
                if header_occurences != HEADER_OCCURENCE_CHECK_LIMIT:
                    HEADER_FREQ_COUNTER[raw_key] += 1

            # Choosing the right header line
            if not MOST_FREQ_HEADER_LINE:
                MOST_FREQ_HEADER_LINE = raw_key

            def find_index_in_most_common(most_common: List[Tuple[str, int]],
                                          line: str) -> int:
                key_list = [x[0] for x in most_common]
                idx = key_list.index(line)
                return idx

            # Counters
            biggest_headers = HEADER_LEN_COUNTER.most_common()
            most_freq_headers = HEADER_FREQ_COUNTER.most_common()

            # Which index
            curr_size_idx = find_index_in_most_common(biggest_headers, raw_key)
            curr_top_size_idx = find_index_in_most_common(
                biggest_headers, MOST_FREQ_HEADER_LINE)
            curr_freq_idx = find_index_in_most_common(most_freq_headers,
                                                      raw_key)
            curr_top_freq_idx = find_index_in_most_common(
                most_freq_headers, MOST_FREQ_HEADER_LINE)
            if (curr_size_idx < curr_top_size_idx) and \
               (curr_freq_idx < curr_top_freq_idx):
                MOST_FREQ_HEADER_LINE = raw_key

    padding = 10
    most_freq_len = len(MOST_FREQ_HEADER_LINE)
    most_freq_len_with_padding = most_freq_len + padding
    # print(HEADER_LEN_COUNTER.most_common())
    if args.align_head:
        if raw_len < most_freq_len_with_padding:
            header_line_str += " " * (most_freq_len_with_padding - raw_len)
        else:
            diff = raw_len - most_freq_len_with_padding
            header_line_str += " " * (diff)

    header_line_str += args.HEADER_SPACER

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
        if args.IGNORE_KEYS and k in args.IGNORE_KEYS:
            continue
        if not v:
            continue
        if not k:
            continue
        if k in headers.keys:
            continue
        k = utils.norm_str(k)
        non_color_k = k
        k = utils.style(k, color=args.colors["K_COLOR"])

        if isinstance(v, dict):
            (new_key_count, nice_str) = utils.nice_print_dict(
                key_count,
                top_spacer,
                v,
                key_color=args.colors["K_COLOR"],
                value_color=value_col,
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
            (new_key_count, nice_str) = utils.nice_print_dict(
                key_count,
                top_spacer,
                nested_d,
                key_color=args.colors["K_COLOR"],
                value_color=value_col,
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
                    args.LEFT_OF_KEY_VALUE,
                    k,
                    utils.style(v, color=value_col),
                    args.RIGHT_OF_KEY_VALUE,
                ))

    if args.raw:
        string_list.append("[{}: {}]".format(
            utils.style("rawline", color=args.colors["K_COLOR"]),
            utils.style(rawline, color=value_col),
        ))
    stack_trace_str = ""
    stack_trace_str_no_col = ""
    # Stack Traces
    if args.FIND_STACKTRACES:

        run_find_stack = True
        if args.PREFIXES:
            run_find_stack = headers.prefix.value.lower() in [
                p.lower() for p in args.PREFIXES
            ]
        if args.IGNORE_PREFIXES:
            run_find_stack = not (headers.prefix.value.lower()
                                  in [p.lower() for p in args.IGNORE_PREFIXES])
        if run_find_stack:
            stack_trace_str = utils.find_stack(
                STACK_TRACE_MAP,
                headers.prefix.value,
                string_dict,
                STACK_TRACE_COLORS,
                log_time,
                args=args,
                is_recording=IS_RECORDING,
            )
            if stack_trace_str:
                stack_trace_str_no_col = utils.remove_col_from_val(stack_trace_str)

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
            if (key in string_dict
                    and key not in args.PREV_RECORDED_STRING_DICT):
                args.PREV_RECORDED_STRING_DICT[key] = string_dict[key]
            if (key in string_dict and
                    string_dict[key] != args.PREV_RECORDED_STRING_DICT[key]):
                changed_keys.append(key)
                change_detected = True
        # Highlight keys
        for key in changed_keys:
            result_str = result_str.replace(
                key,
                utils.style(key, color=args.colors["DETECTED_CHANGE_COLOR"]),
            )
        # Update
        for key in string_dict:
            args.PREV_RECORDED_STRING_DICT[key] = string_dict[key]

    if args.RECORD_KEYS_DIFF and not change_detected:
        will_print = False
        return ("", False)
    if args.HIGHLIGHT_PHRASES:
        for phrase in set(args.HIGHLIGHT_PHRASES):
            if phrase.lower() in result_str.lower():
                start_idx = result_str.lower().find(phrase.lower())
                end_index = start_idx + len(phrase)
                first_section = utils.style(
                    result_str[0:start_idx],
                    color=args.colors["HIGHLIGHT_OFF_COLOR"]
                    if not args.FILTERS else "")
                middle_section = utils.style(
                    result_str[start_idx:end_index],
                    color=args.colors["HIGHLIGHT_COLOR"])
                end_section = utils.style(
                    result_str[end_index:],
                    color=args.colors["HIGHLIGHT_OFF_COLOR"]
                    if not args.FILTERS else "")
                result_str = first_section + middle_section + end_section
    if args.FILTERS:
        if args.filter_any or args.any:
            will_print = any(
                [f.lower() in result_str_no_col.lower() for f in args.FILTERS])
            if stack_trace_str:
                will_print = any(
                    [f.lower() in stack_trace_str_no_col.lower() for f in args.FILTERS])
        else:
            will_print = all(
                [f.lower() in result_str_no_col.lower() for f in args.FILTERS])
            if stack_trace_str:
                will_stack_trace = all(
                    [f.lower() in stack_trace_str_no_col.lower() for f in args.FILTERS])
                if not will_stack_trace:
                    stack_trace_str = ""
    if args.FILTER_OUT:
        for phrase in args.FILTER_OUT:
            if phrase.lower() in result_str_no_col.lower():
                will_print = False
                break
        if stack_trace_str:
            for phrase in args.FILTER_OUT:
                will_not_stack_trace = phrase.lower() in stack_trace_str_no_col.lower()
                if will_not_stack_trace:
                    stack_trace_str = ""
                    break

    count_str = ""
    if will_print:
        if args.WILL_COUNT:
            args.COUNTED_LOGS += 1
            args.t1 = time.time()
            if (args.t1 - args.t0) >= args.TIMING_SECONDS_INTERVAL:
                args.t0 = args.t1
                count_str = (utils.style(
                    "Number of logs after {} seconds: {}".format(
                        args.TIMING_SECONDS_INTERVAL, args.COUNTED_LOGS),
                    color=args.colors["TIMING_COLOR"],
                ) + "\n")
                COUNTED_LOGS = 0
        divider_str = ""
        if args.divider:
            divider_str = args.DIVIDER + "\n"

        if args.title and args.show_title:
            timing_title = ("🕒 ({} secs) ".format(args.TIMING_SECONDS_INTERVAL)
                            if args.WILL_COUNT else "")
            title_str = utils.style(
                "{}{}".format(timing_title, args.title),
                color=Fore.GREEN if (not args.random or args.no_random) else
                STACK_TRACE_COLORS[headers.prefix.value][0] + Fore.BLACK)
            header_line_str = title_str + " " + header_line_str
        if args.ALLOW_RECORD and is_recording:
            header_line_str = "🟢" + " " + header_line_str
        if args.ALLOW_RECORD and not is_recording:
            header_line_str = "🔴" + " " + header_line_str

        # THE PRINT
        header_output = divider_str + count_str + header_line_str + top_spacer + args.SPACER
        thing_to_print = result_str
        if args.flat and not args.no_flat:
            header_output = count_str + header_line_str + args.SPACER
            thing_to_print = result_str.strip()
        # Add the extra stuff
        if args.linespace > 0:
            thing_to_print = thing_to_print + '\n' * args.linespace

        return Output(header_output=header_output,
                      output=thing_to_print,
                      change_detected=change_detected,
                      stacktrace=stack_trace_str)
    return Output(header_output="",
                  output="",
                  change_detected=False,
                  stacktrace=stack_trace_str)


def cool_log(thing_to_print, use_color=True):
    print('\n' * 1)
    if use_color:
        print(utils.style(thing_to_print, color=Fore.YELLOW))
    else:
        print(thing_to_print)
    print('\n' * 1)


def on_press(key):
    global IS_RECORDING
    global INIT_NOT_RECORDING_STATE
    global RECORD_FILE_NAME
    global TITLE
    global COMMON_MSGS
    global COMMON_MSGS_TO_RAWLINE
    global JSON_ARGS_OBJ
    SHOW_COMMON_MSGS = keyboard.Key.f10
    SHOW_ARGS_KEY = keyboard.Key.f11
    ARGS_USED = ' '.join(sys.argv[1:])
    set_filename = False
    try:
        if key == RECORD_KEY:
            IS_RECORDING = not IS_RECORDING
            INIT_NOT_RECORDING_STATE = False
            if not INIT_NOT_RECORDING_STATE and IS_RECORDING:
                if not TITLE:
                    TITLE = "logcat"
                set_filename = True
            if not INIT_NOT_RECORDING_STATE and not IS_RECORDING:
                set_filename = True
            if set_filename:
                curr_files = [
                    int(x.rsplit(".log")[0].rsplit("_")[-1])
                    for x in os.listdir(RECORD_DIR) if TITLE in x
                ]
                curr_files = sorted(curr_files)
                next_inc = 0
                if curr_files:
                    next_inc = int(curr_files[-1]) + 1
                RECORD_FILE_NAME = TITLE + "_{}.log".format(next_inc)
        elif key == SHOW_ARGS_KEY:
            print("\n"*2)
            print("Command to run the following:")
            print()
            if not JSON_ARGS_OBJ:
                cool_log(f"adb logcat | nicelogcat {ARGS_USED}")
            else:
                json_args = []
                for k, v in JSON_ARGS_OBJ.items():
                    args_str = str(k)
                    if not isinstance(v, bool):
                        args_str += f" {v}"
                    json_args.append(args_str)
                cool_log(
                    f"adb logcat | nicelogcat {' '.join(json_args)}"
                )
                print("Or add this to your JSON configs")
                print()
                print(utils.style(json.dumps(JSON_ARGS_OBJ, indent=2), color=Fore.RED))
                print('\n'*2)

        elif key == SHOW_COMMON_MSGS:
            common_str = utils.style("Common Phrases Found (count - msg)",
                                     Fore.YELLOW)
            common_str += "\n" * 3
            msgs = []
            for prefix, msg_counter_dict in COMMON_MSGS.items():
                more_than_1 = {
                    msg: count
                    for msg, count in msg_counter_dict.items() if count > 1
                }
                for msg, count in more_than_1.items():
                    common_str += "\t"
                    common_str += utils.style(prefix, Fore.YELLOW)
                    common_str += " - "
                    common_str += f"{count} - {msg}\n"
                    msgs.append(msg)
            # Common Str Filter out
            common_str += "\n" * 3
            common_str += utils.style(
                "Add this to nicelogcat to filter out these phrases:\n",
                Fore.YELLOW)
            common_str += "\n"
            common_str += ' '.join([
                f"\n-x \"{COMMON_MSGS_TO_RAWLINE[msg].split(' ', 8)[-1].strip()}\""
                + " \\" for msg in msgs
            ])
            common_str = common_str[0:-1]
            cool_log(common_str, False)
    except AttributeError:
        pass

import json
import random
from datetime import datetime
from operator import itemgetter

import adblogs._globals as g
from adblogs.colors import *
from adblogs.regex import *
from adblogs.utils import flatten, check_continue

SEEN_PREFIXES = {}
PREFIX_CHOOSE_COLORS = [Fg.red, Fg.cyan, Fg.magenta, Fg.green]
LINE_SEP = "|"
PROCESS_NAME = "gf-adb"


def parse_json_line(json_str, message=None):
    json_str = json_str.replace("\\", "")
    json_str = json_str.replace('}"', "}")
    json_str = json_str.replace('"{', "{")
    obj = None
    try:
        obj = json.loads(json_str)
    except:
        pass
    return obj


def check_ignore(search_content, largs):
    should_ignore = False
    if largs.find_ignore:
        for ignore_str in largs.find_ignore:
            if largs.find_case_sensitive and any(
                [ignore_str in line for line in search_content]
            ):
                should_ignore = True
            elif not largs.find_case_sensitive and any(
                [ignore_str.lower() in line.lower() for line in search_content]
            ):
                should_ignore = True
    return should_ignore


def pause_line(search_content, largs):
    find_strs = largs.find
    keep_pausing = True
    assert find_strs and isinstance(find_strs, list) and largs.find
    for find_str in largs.find:
        will_check = False
        if (
            largs.find_case_sensitive
            and any([find_str in line for line in search_content])
            and not check_ignore(search_content, largs)
        ):
            will_check = True
        elif (
            not largs.find_case_sensitive
            and any([find_str.lower() in line.lower() for line in search_content])
            and not check_ignore(search_content, largs)
        ):
            will_check = True
        else:
            pass
        if will_check:
            keep_pausing = check_continue(
                "Found line for search: [" + find_str + "]", largs.time_limit
            )
    return keep_pausing


# MAX_SUB_PREFIX = 0

def parse_meta_line(message, largs):
    error = ""
    will_show = True
    prefix = ""

    if any([x in message for x in g.BROKEN_MSGS]):
        return message, error, will_show, prefix
    try:
        json_obj = json.loads(message)
    except:
        # Can't parse json just return
        return message, error, will_show, prefix
    if 'error' in json_obj:
        error = json_obj['error']

    start_brace_idx = json_obj['message'].find('{')
    json_str = None
    parts = []
    obj = {'params': json_obj['params']}
    msg = ""
    if start_brace_idx == -1:
        msg = json_obj['message']
    else:
        msg = json_obj['message'][0:start_brace_idx]
        json_str = json_obj['message'][start_brace_idx:]
    if json_str:
        try:
            inner_obj = json.loads(json_str)
            obj.update(inner_obj)
        except:
            msg = json_obj['message']

    prefix = json_obj['meta']['name']

    if largs.exclude_prefixes and prefix in largs.exclude_prefixes:
        will_show = False

    if prefix not in SEEN_PREFIXES:
        SEEN_PREFIXES[prefix] = random.choice(PREFIX_CHOOSE_COLORS)
    parts.append(style(f"{prefix}", SEEN_PREFIXES[prefix]))
    parts.append(LINE_SEP)
    parts.append(style(msg, g.colors['submessage']))
    parts.append(LINE_SEP)
    if largs.raw:
        obj['raw'] = style(message, Fg.green)

    obj = flatten(obj)
    obj_parts = []
    if "error.stack" in obj:
        error = obj['error.stack'].replace("  ", "\n")
        del obj['error.stack']
    if "error.error.stack" in obj:
        error = obj['error.error.stack'].replace("  ", "\n")
        del obj['error.error.stack']
    if error:
        parts += [style("see error below", Fg.red), LINE_SEP]
    for k, v in obj.items():
        if largs.show_keys and k not in largs.show_keys:
            continue
        if largs.exclude_keys and k in largs.exclude_keys:
            continue
        color = g.colors["value"]
        if largs.highlight_keys and k in largs.highlight_keys:
            color = g.colors["highlight"]
        obj_parts.append(stylekv(str(k), g.colors["key"], str(v), color))
    parts.append(" ".join(obj_parts))
    message = " ".join(parts)
    return message, error, will_show, prefix


def pretty_line(
    date,
    time,
    current_time,
    level,
    prefix,
    message,
    largs,
):
    parts = []

    parts.append(style(str(g.CURRENT_LINE_NUMBER), g.colors["line_number"]))
    parts.append(LINE_SEP)

    parts.append(style(PROCESS_NAME, g.colors["process"]))
    parts.append(LINE_SEP)

    if largs.ip:
        parts.append(style(largs.ip, g.colors["ip"]))
        parts.append(LINE_SEP)

    parts.append(style(date, g.colors["date"]))
    parts.append(LINE_SEP)

    if not largs.no_current_time:
        parts.append(style(current_time, g.colors["current_time"]))
        parts.append(LINE_SEP)

    parts.append(style(time, g.colors["time"]))
    parts.append(LINE_SEP)

    parts.append(style(g.log_levels[level][0], g.log_levels[level][1]))
    parts.append(LINE_SEP)

    if prefix not in SEEN_PREFIXES:
        SEEN_PREFIXES[prefix] = random.choice(PREFIX_CHOOSE_COLORS)
    parts.append(style(prefix, SEEN_PREFIXES[prefix]))

    error = ""
    will_show = True
    if "\"meta\"" in message:
        message, error, will_show, subprefix = parse_meta_line(message, largs)
        will_update_prefix = False
        if largs.show_prefixes and any([prefix in x and ':' in x for x in largs.show_prefixes]):
            will_update_prefix = True
        if largs.exclude_prefixes and any([prefix in x and ':' in x for x in largs.exclude_prefixes]):
            will_update_prefix = True
        if will_update_prefix:
            prefix = prefix + ":" + subprefix
    if largs.show_prefixes and prefix not in largs.show_prefixes:
        return "", error
    if largs.exclude_prefixes and prefix in largs.exclude_prefixes:
        return "", error

    if not will_show:
        return "", error

    if largs.exclude_values:
        for val in largs.exclude_values:
            if val in message:
                return "", error

    if largs.highlight_prefixes and prefix in largs.highlight_prefixes:
        message = remove_col_from_val(message)
        message = style(message, g.colors["highlight"])

    words_to_highlight = []
    if largs.highlight_words:
        # This will only hit the first one!
        for word in largs.highlight_words:
            if word.lower() in message.lower():
                curr_search = message.lower()
                find_index = curr_search.index(word.lower())
                len_word = len(word)
                exact_word = message[find_index: find_index + len_word]
                words_to_highlight.append(exact_word)
    for word in words_to_highlight:
        message = message.replace(word, style(word, g.colors["highlight"]))
    parts.append(LINE_SEP)
    parts.append(style(message, g.colors["message"]))

    line = " ".join(parts)
    return line, error


def line_parse(
    line,
    largs,
):
    global CURRENT_LINE_NUMBER
    new_line = None
    result = line_regex.match(line)
    search_content = [line]
    error = ""
    if result:
        date, time, level, prefix, message = itemgetter(
            "date", "time", "level", "prefix", "message"
        )(result.groupdict())
        date = date.strip()
        time = time.strip()
        level = level.strip()
        prefix = prefix.split(":")[0].strip().replace(" ", "_")
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        message = message.strip()
        if not message:
            return None
        time = time.split(".")[0]
        clean_message = message.replace("\\n", "")
        clean_message = message.replace("\\", "")
        search_content = [prefix, clean_message]

        line, error = pretty_line(
            date,
            time,
            current_time,
            level,
            prefix,
            message,
            largs,
        )
    if largs.filter:
        if any([filter_word in line for filter_word in largs.filter]):
            new_line = line
        else:
            new_line = ""
    else:
        new_line = line
    if new_line:
        # Do the print!
        print(new_line)
        if error:
            num_error_dashes = 150
            error = error.replace('\n\n', '\n')
            error_parts = error.split('\n')
            print(style("-" * num_error_dashes, Fg.red))
            error_str = style(error_parts[0], Fg.red)
            error_str += "\n\t" + "\n\t".join([x for x in error_parts[1:] if x])
            print(error_str)
            print(style("-" * num_error_dashes, Fg.red))
        pass
    if largs.find:
        keep_pausing = pause_line(search_content, largs)
        if not keep_pausing:
            largs.find = []
    return new_line

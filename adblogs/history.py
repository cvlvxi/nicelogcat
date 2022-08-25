import time
import subprocess
import os
import adblogs._globals as g
from pathlib import Path
from pyfzf import FzfPrompt


def write_log_history(parser, largs, log_file):
    ignore_these_strings = (
        g.DEFAULT_FIND_IGNORE + g.DEFAULT_EXCLUDE_PREFIXES + g.DEFAULT_EXCLUDE_KEYS + g.DEFAULT_EXCLUDE_VALUES + g.DEFAULT_HIGHLIGHT_WORDS
    )
    ignore_these_keys = ["log_history_dir", "time_limit"]
    parser_option_mapping = {}
    for item in parser.__dict__["_actions"]:
        dest = item.dest
        if dest not in parser_option_mapping:
            parser_option_mapping[dest] = item.option_strings
    largs_values = {k: v for k, v in largs.__dict__.items() if v}
    if "show_history" in largs_values:
        return
    log_str_parts = ["adblog"]
    item_parts = []
    for k, v in largs_values.items():
        if k in ignore_these_keys:
            continue
        if k not in parser_option_mapping:
            continue
        option = parser_option_mapping[k][0]
        if isinstance(v, list):
            new_v_parts = []
            for item in v:
                if item in ignore_these_strings:
                    continue
                item = item.replace('"', '\\"')
                item = item.replace("'", "\\'")
                item = f'"{str(item)}"'
                new_v_parts.append(item)
            v = " ".join(new_v_parts)
        elif isinstance(v, bool):
            pass
        else:
            # Need to escape quotes
            v = str(v)
            if v in ignore_these_strings:
                continue
            v = v.replace('"', '\\"')
            v = v.replace("'", "\\'")
            v = f'"{v}"'
        if not isinstance(v, bool):
            if v:
                item_parts += [option, v]
        else:
            item_parts += [option]
    log_str_parts = log_str_parts + item_parts
    log_str = " ".join(log_str_parts) + "\n"
    # Check whether last line is the same as this one
    if Path(log_file).exists():
        content = []
        with open(log_file, "r") as f:
            for line in f:
                content.append(line)
        if log_str.strip() == content[-1].strip():
            return
    with open(log_file, "a") as f:
        f.write(log_str)


def show_history(log_file, clear_history):
    if not clear_history:
        fzf = FzfPrompt()
        content = []
        with open(log_file) as f:
            for line in f:
                content.append(line.strip())
        result = fzf.prompt(content, "--tac")
        if result:
            cmd = result[0]
            print(cmd)
            unix_time = int(time.time())
            with open(g.ZSH_HISTORY, "a") as f:
                f.write(f": {unix_time}:0;{cmd}\n")
            subprocess.call(["/bin/zsh", "-i", "-c", cmd])
            # Append this to zsh_history

    else:
        print("Clearing history: " + str(log_file))
        os.system("rm " + str(log_file))

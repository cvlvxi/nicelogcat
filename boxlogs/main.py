import os
from datetime import datetime
from colorama import init, Fore, Back, Style
from traceback import print_exc
from sh import tail
import glob
import time
import json
import argparse
import itertools
from pathlib import Path
import sys
import signal
import hashlib
import subprocess
import select
from bs4 import BeautifulSoup

curr_dir = Path(__file__).parent
tmp_dir = curr_dir / "box_tmp_dir"
html_error_file = tmp_dir / "htmlerror"
logs_dir = "/data/logs"
html_errors = {}

cols = {
    "time": Fore.YELLOW,
    "k": Fore.CYAN,
    "v": Fore.WHITE,
    "h": Back.GREEN + Fore.BLACK,
    "alert": Back.BLACK + Fore.WHITE,
    "info":  Fore.GREEN,
    "warn": Fore.YELLOW,
    "error": Fore.RED
}


assert tmp_dir.exists()
tmp_dir = str(tmp_dir)


def init_remove_files():
    print("Removing files")
    for f in os.listdir(logs_dir):
        os.remove(os.path.join(logs_dir, f))
    for f in os.listdir(str(tmp_dir)):
        if ".html" in f:
            os.remove(os.path.join(tmp_dir, f))


def contains_html(line):
    html_tags = ["<html>", "<br>", "<span>"]
    return any([x in line for x in html_tags])


def write_html(html_error):
    global html_errors

    soup = BeautifulSoup(html_error, 'html.parser')

    # Extract common elements
    title = str(soup.title)
    container = str(soup.find(id='container').find_all(
        "div", {"class": "line"}))
    encoded_str = (title+container).encode()
    html_hash = hashlib.md5(encoded_str).hexdigest()
    short_hash = str(html_hash[0:5])
    print(style("Backend Error: {}. See html file".format(title), Fore.RED))

    if html_hash not in html_errors:
        html_errors[html_hash] = html_error
        html_file_name = str(html_error_file) + "." + short_hash + ".html"
        with open(html_file_name, "w") as f:
            f.write(html_error)


def style(val, color=None):
    val = color + str(val) + Style.RESET_ALL
    return val


def alert(some_str):
    print()
    print(style(some_str, cols["alert"]))
    print()


def flatten(some_list):
    return list(itertools.chain(*some_list))


def flatten_dict(dd, separator='_', prefix=''):
    return {prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
            } if isinstance(dd, dict) else {prefix: dd}


parser = argparse.ArgumentParser(description='BoxLogs')
parser.add_argument('-m', '--show-meta', action="store_true",
                    help="Show Meta fields")
parser.add_argument('-c', '--clear', action="store_true",
                    help="Clear Logs")
parser.add_argument('-a', '--all', action="store_true",
                    help="Start from beginning")
parser.add_argument('-s', '--no-suspend', action="store_true",
                    help="Don't suspend if highlight hit")
parser.add_argument('--h', nargs="*", dest="highlight",
                    action="append", help='Highlight Lines')
parser.add_argument('--f', nargs="*", dest="filter", action="append",
                    help='sum the integers (default: find the max)')

args = parser.parse_args()
if args.filter:
    args.filter = flatten(args.filter)
if args.highlight:
    args.highlight = flatten(args.highlight)
    alert("Will find these items:" + str(args.highlight))
if args.clear:
    print("Removing Files")
    init_remove_files()
    sys.exit(1)

init(autoreset=True)

logdir = "/data/logs/"
continue_strings = ["next", "n", "c", "continue", "cont", " ", "enter"]
stop_suspend = ["s", "stop"]

logs = [os.path.join(logdir, x) for x in os.listdir(logdir)]


def line_loop(line):
    line = line.strip()
    if not line:
        return False
    line_str = ""
    log_level = ""
    if line[0] == "{":
        json_data = json.loads(line)
        json_data = flatten_dict(json_data)
        log_level = json_data.pop("level")
        log_col = cols[log_level] if log_level in cols else Fore.CYAN
        log_level = style(log_level.upper(), log_col)
        if not args.show_meta:
            meta_keys = [k for k in json_data if 'meta' in k]
            for k in meta_keys:
                json_data.pop(k)
        json_str = " ".join(["{}: {}".format(style(k, cols["k"]), style(
            v, cols["v"])) for k, v in json_data.items()])
        if contains_html(line):
            html_error = json_data["error_body"]
            write_html(html_error)
            return False
    else:
        json_str = line
    line_str += log_level + ": " + json_str

    # Filters and highlights
    if args.filter and any([filter_word in line for filter_word in args.filter]):
        return False
    found_highlight = False
    if args.highlight:
        for highlight_word in args.highlight:
            if highlight_word in line:
                found_highlight = True
                line_str = line_str.replace(highlight_word, style(highlight_word, cols["h"]))

    # Main Print
    print(line_str)

    # Suspend loop
    if not args.no_suspend and found_highlight:
        alert("Type: [' '|'c'|'n'] to go to next highlight or ['s'|'stop'] to stop suspending")
        suspend_input = ""
        while True:
            if any([x == suspend_input for x in stop_suspend]):
                args.no_suspend = True
                break
            if any([x == suspend_input for x in continue_strings]):
                break
            suspend_input = input()
            suspend_input = suspend_input.lower()


def print_loop(log_file, log_size_threshold):
    # alert("Starting print_loop, log_file: " + log_file)
    log_path = Path(log_file)
    log_size = 0
    f = subprocess.Popen(['tail', '-F', log_file],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)
    check_size_after_secs = 5
    start_time = time.time()
    while True:
        if p.poll(1):
            line = f.stdout.readline()
            will_exit = line_loop(line.decode())
            if will_exit:
                return
        else:
            curr_time = time.time()
            if (curr_time - start_time) > check_size_after_secs:
                log_size = log_path.stat().st_size
                if log_size > log_size_threshold:
                    return


def main_loop():
    log_size_threshold_1mb = 1000000
    log_files = list(
        filter(os.path.isfile, glob.glob(os.path.join(logdir, "*"))))
    log_files.sort(key=lambda x: os.path.getmtime(x))

    prev_log_files = log_files[:-1]

    if args.all:
        for log_file in prev_log_files:
            with open(log_file, "r") as f:
                prev_logs = f.read()
                for line in prev_logs.split("\n"):
                    line_loop(line)

    while True:
        log_files = list(
            filter(os.path.isfile, glob.glob(os.path.join(logdir, "*"))))
        log_files.sort(key=lambda x: os.path.getmtime(x))
        log_file = log_files[-1]
        print_loop(log_file, log_size_threshold_1mb)


if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        print_exc()

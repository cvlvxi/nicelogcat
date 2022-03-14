import os
from datetime import datetime
from colorama import init, Fore, Back, Style
from traceback import print_exc
from sh import tail, glob
import json
import argparse
import itertools
from pathlib import Path
import sys
import signal
import hashlib
from bs4 import BeautifulSoup

CURR_LINE = ""
PREV_LINE = ""

curr_dir = Path(__file__).parent
tmp_dir = curr_dir / "box_tmp_dir"
curr_line_file = tmp_dir / "currline.txt"
html_error_file = tmp_dir / "htmlerror"
logs_dir = "/data/logs"
html_errors = {}

cols = {
    "time": Fore.YELLOW,
    "k": Fore.CYAN,
    "v": Fore.WHITE,
    "h": Back.GREEN + Fore.BLACK,
    "alert": Back.WHITE + Fore.BLACK
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
    container = str(soup.find(id='container').find_all("div", {"class": "line"}))
    encoded_str = (title+container).encode()
    html_hash = hashlib.md5(encoded_str).hexdigest()
    short_hash = str(html_hash[0:5])

    if html_hash not in html_errors:
        html_errors[html_hash] = html_error
        html_file_name = str(html_error_file) + "." + short_hash  + ".html"
        with open(html_file_name, "w") as f:
            f.write(html_error)


def alert(some_str):
    print()
    print()
    print(style(some_str, cols["alert"]))


def flatten(some_list):
    return list(itertools.chain(*some_list))


def flatten_dict(dd, separator='_', prefix=''):
    return {prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
            } if isinstance(dd, dict) else {prefix: dd}


def handler(signum, frame):
    alert("Saving curr_line to: " + str(curr_line_file))
    with open(str(curr_line_file), "w") as f:
        f.write(CURR_LINE)
    sys.exit(1)


signal.signal(signal.SIGINT, handler)

parser = argparse.ArgumentParser(description='BoxLogs')
parser.add_argument('-c', '--clear', action="store_true",
                    help="Clear Logs")
parser.add_argument('-n', '--new', action="store_true",
                    help="Start logging new")
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
if curr_line_file.exists():
    if args.new and curr_line_file.exists():
        os.remove(str(curr_line_file))
    else:
        with open(str(curr_line_file), "r") as f:
            PREV_LINE = f.read().strip()
            if not PREV_LINE:
                args.new = True
if args.clear:
    print("Removing Files")
    init_remove_files()
    sys.exit(1)

init(autoreset=True)


def style(val, color=None):
    val = color + str(val) + Style.RESET_ALL
    return val


logdir = "/data/logs/"
continue_strings = ["next", "n", "c", "continue", "cont", " ", "enter"]
stop_suspend = ["s", "stop"]

logs = [os.path.join(logdir, x) for x in os.listdir(logdir)]


def main_loop():
    start_logging = False
    start_logging_limit = 10000
    count = 0
    for line in tail("-f", glob("/data/logs/*"),  _iter=True):
        CURR_LINE = line
        if not start_logging and not args.new and PREV_LINE:
            start_logging = PREV_LINE in CURR_LINE
        else:
            start_logging = True
        if count >= start_logging_limit:
            start_logging = True
        if not start_logging:
            continue
        now = datetime.now()
        line = line.strip()
        if not line:
            continue
        line_str = ""
        line_str += style(now.ctime(), cols["time"])
        if line[0] == "{":
            json_data = json.loads(line)
            json_data = flatten_dict(json_data)
            json_str = " ".join(["{}: {}".format(style(k, cols["k"]), style(
                v, cols["v"])) for k, v in json_data.items()])
            if contains_html(line):
                html_error = json_data["error_body"]
                write_html(html_error)
        else:
            json_str = line
        line_str += " " + json_str

        # Main Print
        print(line_str)

        # Filters and highlights
        if args.filter and any([filter_word in line for filter_word in args.filter]):
            continue
        found_highlight = False
        if args.highlight:
            for highlight_word in args.highlight:
                if highlight_word in line:
                    found_highlight = True
                    line_str = line_str.replace(
                        highlight_word, style(highlight_word, cols["h"]))
        # Suspend loop
        if not args.no_suspend and found_highlight:

            alert("Type one of: " + ",".join(continue_strings))
            alert("Type one of: " + ",".join(stop_suspend) + " to stop suspending")

            suspend_input = ""
            while True:
                if any([x == suspend_input for x in stop_suspend]):
                    args.no_suspend = True
                    break
                if any([x == suspend_input for x in continue_strings]):
                    break
                suspend_input = input()
                suspend_input = suspend_input.lower()
        count += 1


if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        print_exc()

import os
from datetime import datetime
from colorama import init, Fore, Back, Style
from sh import tail, glob
import json
import argparse
import itertools


def flatten(some_list):
    return list(itertools.chain(*some_list))


def flatten_dict(dd, separator ='_', prefix =''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }


parser = argparse.ArgumentParser(description='BoxLogs')
parser.add_argument('--h', nargs="*", dest="highlight", action="append", help='Highlight Lines')
parser.add_argument('--f', nargs="*", dest="filter", action="append", help='sum the integers (default: find the max)')

args = parser.parse_args()
if args.filter:
    args.filter = flatten(args.filter)
if args.highlight:
    args.highlight = flatten(args.highlight)

init(autoreset=True)

def style(val, color=None):
    val = color + str(val) + Style.RESET_ALL
    return val

cols = {
    "time": Fore.YELLOW,
    "k": Fore.CYAN,
    "v": Fore.WHITE,
    "h": Back.GREEN + Fore.BLACK
}


logdir="/data/logs/"

logs = [os.path.join(logdir, x) for x in os.listdir(logdir)]

for line in tail("-f", glob("/data/logs/*"),  _iter=True):
    now = datetime.now()
    line = line.strip()
    if not line:
        continue
    line_str = ""
    line_str += style(now.ctime(), cols["time"])
    if line[0] == "{":
        json_data = json.loads(line)
        json_data = flatten_dict(json_data)
        json_str = " ".join(["{}: {}".format(style(k, cols["k"]), style(v, cols["v"])) for k, v in json_data.items()])
    else:
        json_str = line
    line_str += " " + json_str

    # Filters and highlights
    if args.filter and any([filter_word in line for filter_word in args.filter]):
        continue
    if args.highlight:
        for highlight_word in args.highlight:
            if highlight_word in line:
                line_str = line_str.replace(highlight_word, style(highlight_word, cols["h"]))
    print(line_str)



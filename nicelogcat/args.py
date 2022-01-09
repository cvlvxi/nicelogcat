import argparse
import sys
import argcomplete
from constants import COLOR_STRS
from colorama import Fore

parser = argparse.ArgumentParser(description="Bleh")
parser.add_argument("--title", default="", type=str, help="Title to show")
parser.add_argument(
    "--suspend-util", default=None, type=str, help="Suspend until this is found"
)
parser.add_argument(
    "--spacer",
    default="space",
    choices=["newline", "space", "tab", "pipe"],
    help="spacer to use",
)
parser.add_argument(
    "--linespace", type=int, default=0, help="Number of spaces between lines"
)
parser.add_argument("--divider", action="store_true", help="Add a divider per line")
parser.add_argument(
    "--title-in-header", action="store_true", help="Add title to header"
)
parser.add_argument("--raw", action="store_true", help="Include raw line")
parser.add_argument(
    "--keys", nargs="*", required=False, default=None, help="Highlight keys"
)
parser.add_argument(
    "--show-title-every-line", action="store_true", help="Show title every line"
)
parser.add_argument(
    "--title-line-color",
    default=Fore.BLUE,
    choices=COLOR_STRS,
    help="Color to use if showing title every line",
)
parser.add_argument(
    "--highlight",
    nargs="*",
    required=False,
    default=None,
    help="Highlight these phrase",
)
parser.add_argument(
    "--filters", nargs="*", default=None, type=str, help="List of filters"
)
parser.add_argument(
    "--filter-all", action="store_true", help="Filters Must filter all otherwise any"
)
parser.add_argument(
    "--level", nargs="*", default=None, type=str, help="Only these levels"
)
parser.add_argument(
    "--prefix", nargs="*", default=None, type=str, help="Only these Prefix"
)
parser.add_argument(
    "--ignore-prefix", nargs="*", default=None, type=str, help="Ignore These Prefix"
)
parser.add_argument(
    "--ignore-keys", nargs="*", default=None, type=str, help="Ignore These Keys"
)
parser.add_argument("--per-line", type=int, default=4, help="Keys per line")
parser.add_argument(
    "--time-per-secs",
    type=int,
    default=0,
    help="Will time how many logs called every [internal] secs",
)

parser.add_argument(
    "--header-spacer",
    default="space",
    choices=["newline", "space"],
    help="Heading spacer between log",
)
parser.add_argument(
    "--filterout",
    nargs="*",
    default=None,
    type=str,
    help="List of filters to filter out",
)

parser.add_argument(
    "--record-logs", action="store_true", help="Allow recording based on key event"
)

argcomplete.autocomplete(parser)
args = parser.parse_args()

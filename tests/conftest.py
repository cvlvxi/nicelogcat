import pathlib
import pytest
from colorama import Fore, Back
from argparse import ArgumentParser
from nicelogcat.args import ncparser, get_args, post_process_args

data = pathlib.Path(__file__).parent / "testdata.log"


@pytest.fixture()
def logstream(scope="function"):
    fh = open(data, "rb")
    yield fh
    fh.close


def add_defaults(args):
    colors = {
        "HEADER_STR_COLOR": Back.YELLOW + Fore.BLACK,
        "LEVEL_WARN_COLOR": Back.BLACK + Fore.YELLOW,
        "LEVEL_ERROR_COLOR": Back.BLACK + Fore.RED,
        "LEVEL_INFO_COLOR": Back.BLACK + Fore.GREEN,
        "TIME_COLOR": Fore.MAGENTA,
        "CURRENT_TIME_COLOR": Fore.RED,
        "PREFIX_COLOR": Fore.GREEN,
        "TITLE_COLOR": Fore.MAGENTA,
        "HIGHLIGHT_COLOR": Back.BLACK + Fore.GREEN,
        "V_COLOR": Fore.WHITE,
        "K_COLOR": Fore.CYAN,
        "STACK_MSG_COLOR": Fore.GREEN,
        "PATH_COLOR": Fore.LIGHTMAGENTA_EX,
        "TIMING_COLOR": Back.RED + Fore.BLACK,
        "DETECTED_CHANGE_COLOR": Back.RED + Fore.BLACK,
    }
    args.colors = colors
    return args


@pytest.fixture()
def args_prefix() -> ArgumentParser:
    parser = ncparser()
    args = post_process_args(add_defaults(get_args(parser, ['-p', 'AppOps'])))
    return args


@pytest.fixture()
def args_title() -> ArgumentParser:
    parser = ncparser()
    args = post_process_args(add_defaults(get_args(parser, [
        '-p', 'AppOps',
        '--title', 'hello'
    ])))
    return args

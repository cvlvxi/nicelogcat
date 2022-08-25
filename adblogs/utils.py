import subprocess
import sys
from adblogs.colors import *
from inputimeout import inputimeout, TimeoutOccurred


def a_split(arg_val):
    if arg_val:
        new_val = []
        if isinstance(arg_val, list):
            for val in arg_val:
                if isinstance(val, list):
                    new_val += val
        else:
            new_val.append(val)
        return new_val
    else:
        return []


def flatten(dictionary, parent_key=False, separator="."):
    """
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        # new_key = key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def check_continue(msg="", time_limit_secs=5):

    break_keys = ["b"]
    continue_keys = [" ", "c", "space"]
    quit_keys = ["q", "s", "skip"]
    help = "{} to continue {} to break {} to quit. {} secs left...".format(
        continue_keys, break_keys, quit_keys, time_limit_secs
    )
    if msg:
        print(style(msg + " " + help, Bg.red + Fg.white))
    else:
        print(help)
    keep_pausing = True
    try:
        get_input = inputimeout(prompt=">> ", timeout=time_limit_secs)
        while True:
            if get_input.lower() in continue_keys:
                print("continuing")
                break
            elif get_input.lower() in break_keys:
                print("breaking")
                keep_pausing = False
                break
            elif get_input.lower() in quit_keys:
                sys.exit(1)
            else:
                get_input = inputimeout(prompt=">> ", timeout=time_limit_secs)
    except TimeoutOccurred:
        # Allow to just keep_pausing for next
        pass

    return keep_pausing

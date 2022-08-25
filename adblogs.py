from pynput import keyboard
import adblogs._globals as g
from adblogs.colors import *
from adblogs.history import show_history
from adblogs.line import line_parse
from adblogs.keyinput import on_press, on_release
from adblogs.adb import adb_logs
from adblogs.arguments import log_args


def print_next_line_loop(largs):
    adb_logs_generator = adb_logs(largs.ip)
    while True:
        if not g.pause_logging:
            line = next(adb_logs_generator)
            new_line = line_parse(
                line,
                largs,
            )
            if new_line:
                g.CURRENT_LINE_NUMBER += 1
                g.LINE_BUFFER.append(new_line)


def main():
    largs = log_args()
    if largs.debug:
        breakpoint()
    if largs.show_history or largs.clear_history:
        show_history(largs.log_history_file, largs.clear_history)
        return
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    print_next_line_loop(largs)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

import sys
import schedule
import traceback
import time
import os
from adbutils import adb
from colorama import Fore, Back
from pynput import keyboard
from rich.console import Console
from rich.text import Text
from threading import Thread
from typing import Optional

from nicelogcat.arguments import NiceLogCatArgs, Args
from nicelogcat.logcat import main_loop, on_press, Output
from nicelogcat.utils import style, remove_col_from_val, pstyle

highlight_col = Fore.BLACK + Back.YELLOW
healthcheck_every_secs = 30

def check_continue(msg: str = "", dont_quit=False) -> bool:
    if msg: 
        pstyle(msg, Fore.RED)
    continue_keys = [" ", "c", "space"]
    quit_keys = ["q", "s", "skip"]
    print(f"Either type: {continue_keys} to continue or {quit_keys} to quit")
    get_input = input()

    while True:
        if get_input.lower() in continue_keys:
            print("continuing")
            break;
        elif get_input.lower() in quit_keys:
            # print("quitting")
            if dont_quit:
                return False
            else:
                sys.exit(1)
        else:
            get_input = input()
    return True

def prepare():
    args, extra_args  = NiceLogCatArgs.get_arguments()
    from_log = extra_args.from_log
    console = Console()
    if not args.record.off:
        while True:
            line = next(sys.stdin.buffer.raw)
            line = line.decode(errors="ignore")
            line = line.strip()
            will_pause = False
            try:
                out: Optional[Output] = main_loop(args, line=line, extra_args=extra_args)
                if not out:
                    continue
                if not args.stacktrace.off:
                    stack_trace = out.stacktrace.strip()
                    if stack_trace:
                        console.print(Text.from_ansi(out.stacktrace))
                else:
                    line = out.header_output + out.output
                    if from_log:
                        raw_line = remove_col_from_val(out.header_output + out.output)
                        norm_raw = raw_line.replace('  ', ' ')
                        norm_from = from_log.replace('  ', ' ')
                        if norm_from in norm_raw:
                            line = style(raw_line, highlight_col)
                            will_pause = True
                    console.print(Text.from_ansi(line))
                    if will_pause:
                        time.sleep(10)
            except Exception:
                console.print(traceback.print_exc())


def check_alive():
    def adb_check_device():
        devices = adb.device_list()
        if len(devices) == 0:
            print(style('Healthcheck: ❌ - Device down', color=Fore.RED))
            sys.exit(1)
        else:
            print(style(f'Healthcheck: ✅ - Device up {devices}', color=Fore.GREEN))
    schedule.every(healthcheck_every_secs).seconds.do(adb_check_device)
    while True:
        schedule.run_pending()
        time.sleep(1)



def main():
    job_thread = Thread(target=check_alive)
    job_thread.daemon = True
    job_thread.start()
    prepare()


if __name__ == "__main__":
    main()

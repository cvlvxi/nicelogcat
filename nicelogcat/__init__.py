
import asyncio
import sys
import schedule
import traceback
import time
from adbutils import adb
from colorama import Fore, Back
from pynput import keyboard
from rich.console import Console
from rich.text import Text
from threading import Thread

from nicelogcat.arguments import NiceLogCatArgs, Args
from nicelogcat.logcat import main_loop, on_press, Output
from nicelogcat.utils import style, remove_col_from_val

highlight_col = Fore.BLACK + Back.YELLOW

async def prepare():
    args, extra_args  = NiceLogCatArgs.get_arguments()
    from_log = extra_args.from_log
    console = Console()
    if not args.record.off:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                async for out in main_loop(args, stream=sys.stdin.buffer.raw, extra_args=extra_args):
                    out: Output
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
                        console.print(Text.from_ansi(line))
                listener.join()
            except Exception:
                console.print(traceback.print_exc())


def logcat():
    asyncio.run(prepare())


def check_alive():
    devices = adb.device_list()
    if len(devices) == 0:
        print(style('Healthcheck: ❌ - Device down', color=Fore.RED))
        sys.exit(1)
    else:
        print(style(f'Healthcheck: ✅ - Device up {devices}', color=Fore.GREEN))


def main():
    check_alive()
    job_thread = Thread(target=logcat)
    job_thread.daemon = True
    job_thread.start()
    schedule.every(60).seconds.do(check_alive)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()


import asyncio
import sys
import schedule
import traceback
import time
from adbutils import adb
from colorama import Fore
from pynput import keyboard
from rich.console import Console
from rich.text import Text
from threading import Thread

from nicelogcat.arguments import NiceLogCatArgs, Args
from nicelogcat.logcat import main_loop, on_press, Output
from nicelogcat.utils import style


async def prepare():
    args: Args = NiceLogCatArgs.get_arguments()
    console = Console()
    if not args.record.off:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                async for out in main_loop(args, stream=sys.stdin.buffer.raw):
                    out: Output
                    if not args.stacktrace.off:
                        console.print(Text.from_ansi(out.stacktrace))
                    else:
                        console.print(
                            Text.from_ansi(out.header_output + out.output))
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

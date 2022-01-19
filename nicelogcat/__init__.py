import sys
import asyncio
import traceback
from pynput import keyboard
from colorama import Fore, Back
from .args import main_args, ncparser
from .logcat import main_loop, on_press, Output

__all__ = ['ncparser']


def main():
    asyncio.run(prepare())


async def prepare():
    args = main_args()
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
    if args.ALLOW_RECORD:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                async for out in main_loop(args, stream=sys.stdin.buffer.raw):
                    out: Output
                    if args.FIND_STACKTRACES:
                        print(out.stacktrace)
                    else:
                        print(out.output)
                main_loop(args, stream=sys.stdin.buffer.raw)
                listener.join()
            except Exception:
                print(traceback.print_exc())
    else:
        async for log in main_loop(args, stream=sys.stdin.buffer.raw):
            print(log)


if __name__ == "__main__":
    main()

import sys
import asyncio
import traceback
from pynput import keyboard
from colorama import Fore, Back
from rich.console import Console
from rich.text import Text
from .args import main_args, ncparser
from .logcat import main_loop, on_press, Output

__all__ = ['ncparser']


def main():
    asyncio.run(prepare())


async def prepare():
    args, json_args_obj = main_args()
    colors = {
        "HEADER_STR_COLOR": Back.YELLOW + Fore.BLACK,
        "LEVEL_WARN_COLOR": Back.BLACK + Fore.YELLOW,
        "LEVEL_ERROR_COLOR": Back.BLACK + Fore.RED,
        "LEVEL_INFO_COLOR": Back.BLACK + Fore.GREEN,
        "TIME_COLOR": Fore.LIGHTBLACK_EX + Back.YELLOW,
        "CURRENT_TIME_COLOR": Fore.RED,
        "PREFIX_COLOR": Fore.GREEN,
        "TITLE_COLOR": Fore.MAGENTA,
        "HIGHLIGHT_COLOR": Back.RED + Fore.BLACK,
        "HIGHLIGHT_OFF_COLOR": Fore.BLACK + Back.YELLOW,
        "V_COLOR": Fore.WHITE,
        # "K_COLOR": Back.RED + Fore.BLACK,
        "K_COLOR": Fore.GREEN,
        "STACK_MSG_COLOR": Fore.GREEN,
        "PATH_COLOR": Fore.LIGHTMAGENTA_EX,
        "TIMING_COLOR": Back.RED + Fore.BLACK,
        "DETECTED_CHANGE_COLOR": Back.RED + Fore.BLACK,
    }
    console = Console()
    args.colors = colors
    if args.ALLOW_RECORD:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                async for out in main_loop(args, stream=sys.stdin.buffer.raw, json_args_obj=json_args_obj):
                    out: Output
                    if args.FIND_STACKTRACES:
                        console.print(Text.from_ansi(out.stacktrace))
                    else:
                        console.print(Text.from_ansi(out.header_output + out.output))
                # main_loop(args, stream=sys.stdin.buffer.raw,  json_args_obj=json_args_obj)
                listener.join()
            except Exception:
                console.print(traceback.print_exc())


if __name__ == "__main__":
    main()

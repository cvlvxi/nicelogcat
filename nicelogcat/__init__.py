import sys
import traceback
import asyncio
from pynput import keyboard
from rich.console import Console
from rich.text import Text

from nicelogcat.arguments import get_arguments, Args
from nicelogcat.logcat import main_loop, on_press, Output


def main():
    asyncio.run(prepare())


async def prepare():
    args: Args = get_arguments()
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


if __name__ == "__main__":
    main()

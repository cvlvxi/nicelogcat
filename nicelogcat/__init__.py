import sys
import traceback
import asyncio
from pynput import keyboard
from rich.console import Console
from rich.text import Text

from nicelogcat.arguments import get_arguments, Args
from nicelogcat.logcat import main_loop, on_press, Output

__all__ = ['ncparser']


def main():
    asyncio.run(prepare())


async def prepare():
    args: Args = get_arguments()
    dog_args = args
    breakpoint()
    console = Console()
    if args.ALLOW_RECORD:
        with keyboard.Listener(on_press=on_press) as listener:
            try:
                async for out in main_loop(args, stream=sys.stdin.buffer.raw):
                    out: Output
                    if args.FIND_STACKTRACES:
                        console.print(Text.from_ansi(out.stacktrace))
                    else:
                        console.print(
                            Text.from_ansi(out.header_output + out.output))
                listener.join()
            except Exception:
                console.print(traceback.print_exc())


if __name__ == "__main__":
    main()

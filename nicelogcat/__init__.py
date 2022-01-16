import sys
from colorama import Fore, Back
from nicelogcat.args import get_args
from nicelogcat.logcat import main_loop

def main():
    args = get_args()
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
    # if args.ALLOW_RECORD:
    #     with keyboard.Listener(on_press=on_press) as listener:
    #         try:
    #             main_loop(args)
    #             listener.join()
    #         except:
    #             pass
    # else:
    main_loop(args, stream=sys.stdin.buffer.raw)


if __name__ == "__main__":
    main()

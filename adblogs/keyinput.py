from pyfzf import FzfPrompt
from pynput import keyboard
from pathlib import Path

import adblogs._globals as g
import subprocess


combo1 = [{keyboard.Key.ctrl, keyboard.KeyCode(vk=47)}]  # ctrl + /
combo2=  [{keyboard.Key.ctrl, keyboard.KeyCode(vk=39)}]  # ctrl + '

pressed_vks = set()


def show_prompt():
    g.pause_logging = True
    fzf = FzfPrompt()
    fzf_options = '--prompt=">> "'
    fzf_options += " --ansi"
    fzf_options += " --tac"
    fzf_options += " --exact"
    fzf_options += " -i"
    fzf_options += " --preview 'echo {}'"
    fzf_options += " --preview-window down,wrap,8%"
    fzf_options += " --color 'bg+:#000000,bg:#313131,preview-bg:#000000,border:#778899'"
    try:
        result = fzf.prompt(choices=list(g.LINE_BUFFER), fzf_options=fzf_options)
    except:
        pass
    g.pause_logging = False


def execute():
    """My function to execute when a combination is pressed"""
    show_prompt()

def test():
    script = Path(__file__).parent / "bin" / "args_switcher.py"
    subprocess.call(["python", script])


def get_vk(key):
    """
    Get the virtual key code from a key.
    These are used so case/shift modifications are ignored.
    """
    return key.vk if hasattr(key, "vk") else key.value.vk


def pressed_combo(combinations):
    found = False
    for combo in combinations:
        found = all([get_vk(key) in pressed_vks for key in combo])
        if found:
            break
    return found


def on_press(key):
    """When a key is pressed"""
    vk = get_vk(key)  # Get the key's v
    pressed_vks.add(vk)  # Add it to the set of currently pressed keys

    if pressed_combo(combo1):
        execute()  # If they are all pressed, call your function
    
    elif pressed_combo(combo2):
        test()
        


def on_release(key):
    """When a key is released"""
    vk = get_vk(key)  # Get the key's vk
    try:
        # Remove it from the set of currently pressed keys
        pressed_vks.remove(vk)
    except:
        pass

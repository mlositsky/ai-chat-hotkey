#!/usr/bin/env python

import platform

from modules.common import HotkeyCombination

system = platform.system()
if system == "Darwin":
    print("macOS detected")
    hotkey_combination = HotkeyCombination('alt+space')
    from modules.mac import init_listener
elif system == "Windows":
    print("Windows detected")
    hotkey_combination = HotkeyCombination('ctrl+shift+q')
    from modules.win import init_listener
else:
    print(f"Other: {system}")
    exit()

init_listener(hotkey_combination)

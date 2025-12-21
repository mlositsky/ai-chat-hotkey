#!/usr/bin/env python

import platform

system = platform.system()
if system == "Darwin":
    print("macOS detected")
    from modules.mac import init_listener
elif system == "Windows":
    print("Windows detected")
    from modules.win import init_listener
else:
    print(f"Other: {system}")
    exit()

init_listener()

# SPDX-FileCopyrightText: 2021 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys example: Adobe Photoshop for Windows

from adafruit_hid.keycode import Keycode # REQUIRED if using Keycode.* values

app = {                       # REQUIRED dict, must be named 'app'
    'name' : 'Premiere', # Application name
    'macros' : [              # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0xBB51FB, 'Undo', [Keycode.CONTROL, 'z']),
        (0x000040, 'Cut', 'c'),   # Cycle brush modes
        (0xC402ff, 'Redo', [Keycode.CONTROL, 'Z']),
        # 2nd row ----------
        (0x0bfaff, 'Link', [Keycode.CONTROL, 'l']),     # Default colors
        (0x86f9fd, 'UnLink', [Keycode.CONTROL, 'l']), # Cycle rect/ellipse marquee (select)
        (0xFf0004, 'Delete', [Keycode.DELETE]),  # Cycle eraser modes
        # 3rd row ----------
        (0x101010, 'Mark', 'm'),    # Swap foreground/background colors
        (0x101010, 'UnMark', [Keycode.CONTROL, Keycode.ALT, 'm']),    # Move layer
        (0x000040, 'Next Mark', 'M'),    # Cycle fill/gradient modes
        # 4th row ----------
        (0x00ff61, 'Save', [Keycode.CONTROL, 's']), # Cycle eyedropper/measure modes
        (0x101010, 'Group', [Keycode.CONTROL, 'g']),    # Cycle "magic wand" (selection) modes
        (0x000040, 'UnGroup', [Keycode.CONTROL, 'G']),    # Cycle "healing" modes
        # Encoder button ---
        (0x000000, '', [Keycode.CONTROL, 'S']) # Save for web
    ]
}

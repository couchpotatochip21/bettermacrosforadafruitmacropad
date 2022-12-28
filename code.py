# SPDX-FileCopyrightText: 2021 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
A macro/hotkey program for Adafruit MACROPAD. Macro setups are stored in the
/macros folder (configurable below), load up just the ones you're likely to
use. Plug into computer's USB port, use dial to select an application macro
set, press MACROPAD keys to send key sequences and other USB protocols.
"""

# pylint: disable=import-error, unused-import, too-few-public-methods

import os
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_macropad import MacroPad


# CONFIGURABLES ------------------------

MACRO_FOLDER = "/macros"
IMAGES_FOLDER = "/images"
DEFAULT_IMAGE = f"{IMAGES_FOLDER}/default_animation.bmp"
ICON_DURATION = 1 # show icon for 1 second
FRAME_DURATION = 0.05


# IMAGE ANIMATION ----------------------

"""
All icons are a multiple of 64 high.
Animations are vertical sprite sheets.
"""

ICON_HEIGHT = 64 # all icons are 64 high

image_file = None
current_image_path = ""

def display_image(icon_file):
    global image_file, current_image_path
    enc_position = macropad.encoder
    image_file_path = f"{IMAGES_FOLDER}/{icon_file}"
    # check image exists
    try:
        os.stat(image_file_path)
    except OSError:
        image_file_path = DEFAULT_IMAGE
    # load image
    if current_image_path != image_file_path:
        if image_file is not None:
            image_file.close()
            image_file = None
        current_image_path = image_file_path
        image_file = open(image_file_path, "rb")
    bitmap = displayio.OnDiskBitmap(image_file)
    # find the animations
    frame_count = 1
    height_count = bitmap.height // ICON_HEIGHT
    if height_count > 1:
        frame_count = height_count
    # make sprite
    sprite = displayio.TileGrid(
        bitmap,
        pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter()),
        tile_width=bitmap.width,
        tile_height=ICON_HEIGHT,
    )
    # show it
    sprite_group = displayio.Group()
    sprite_group.append(sprite)
    sprite_group.x = (128 - bitmap.width) // 2
    macropad.display.show(sprite_group)
    # animate it
    t0 = time.monotonic()
    loop = True
    while loop and time.monotonic() < t0 + ICON_DURATION:
        for current_frame in range(frame_count):
            sprite_group[0][0] = current_frame
            macropad.display.refresh()
            if macropad.encoder != enc_position:
                loop = False
                break
            time.sleep(FRAME_DURATION)
    if not loop:
        return False
    # back to normal
    return True

# CLASSES AND FUNCTIONS ----------------

class App:
    """ Class representing a host-side application, for which we have a set
        of macro sequences. Project code was originally more complex and
        this was helpful, but maybe it's excessive now?"""
    def __init__(self, appdata, index):
        self.index = index
        self.name = appdata['name']
        self.macros = appdata['macros']
        self.icon = appdata.get('icon', f"{index}.bmp")

    def switch(self):
        """ Activate application settings; update OLED labels and LED
            colors. """
        # stop everything
        macropad.keyboard.release_all()
        macropad.consumer_control.release()
        macropad.mouse.release_all()
        macropad.stop_tone()
        # switch the key LEDs
        for i in range(12):
            if i < len(self.macros): # Key in use, set label + LED color
                macropad.pixels[i] = self.macros[i][0]
            else:  # Key not in use, no label or LED
                macropad.pixels[i] = 0
        macropad.pixels.show()
        # show/animate the icon
        result = display_image(self.icon)
        # return if interrupted
        if not result:
            return False
        # show the menu
        for i in range(12):
            if i < len(self.macros): # Key in use, set label + LED color
                group[i].text = self.macros[i][1]
            else:  # Key not in use, no label or LED
                group[i].text = ''
        group[13].text = self.name   # Application name
        macropad.display.show(group)
        macropad.display.refresh()
        return True


# INITIALIZATION -----------------------

macropad = MacroPad()
macropad.display.auto_refresh = False
macropad.pixels.auto_write = False
firsttime = False

# Set up displayio group with all the labels
group = displayio.Group()
for key_index in range(12):
    x = key_index % 3
    y = key_index // 3
    group.append(label.Label(terminalio.FONT, text='', color=0xFFFFFF,
                             anchored_position=((macropad.display.width - 1) * x / 2,
                                                macropad.display.height - 1 -
                                                (3 - y) * 12),
                             anchor_point=(x / 2, 1.0)))
group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
group.append(label.Label(terminalio.FONT, text='', color=0x000000,
                         anchored_position=(macropad.display.width//2, -2),
                         anchor_point=(0.5, 0.0)))
macropad.display.show(group)

# Load all the macro key setups from .py files in MACRO_FOLDER
apps = []
app_index = 0
files = os.listdir(MACRO_FOLDER)
files.sort()
for filename in files:
    if filename.endswith('.py') and not filename.startswith('._'):
        try:
            module = __import__(MACRO_FOLDER + '/' + filename[:-3])
            apps.append(App(module.app, app_index))
            app_index += 1
        except (SyntaxError, ImportError, AttributeError, KeyError, NameError,
                IndexError, TypeError) as err:
            print("ERROR in", filename)
            import traceback
            traceback.print_exception(err, err, err.__traceback__)

if not apps:
    group[13].text = 'NO MACRO FILES FOUND'
    macropad.display.refresh()
    while True:
        pass

last_position = None
last_encoder_switch = macropad.encoder_switch_debounced.pressed
app_index = 0
apps[app_index].switch()

hide_image_time = 0

# MAIN LOOP ----------------------------

while True:
    # Read encoder position. If it's changed, switch apps.
    position = macropad.encoder
    if position != last_position:
        whichframe = 0
        app_index = position % len(apps)
        result = apps[app_index].switch()
        last_position = position
        # if the animation was interrupted by rotating the encoder
        # don't display the menu, ignore the keys, just restart the loop
        if not result:
            continue

    # Handle encoder button. If state has changed, and if there's a
    # corresponding macro, set up variables to act on this just like
    # the keypad keys, as if it were a 13th key/macro.
    macropad.encoder_switch_debounced.update()
    encoder_switch = macropad.encoder_switch_debounced.pressed
    if encoder_switch != last_encoder_switch:
        last_encoder_switch = encoder_switch
        if len(apps[app_index].macros) < 13:
            continue    # No 13th macro, just resume main loop
        key_number = 12 # else process below as 13th macro
        pressed = encoder_switch
    else:
        event = macropad.keys.events.get()
        if not event or event.key_number >= len(apps[app_index].macros):
            continue # No key events, or no corresponding macro, resume loop
        key_number = event.key_number
        pressed = event.pressed

    # If code reaches here, a key or the encoder button WAS pressed/released
    # and there IS a corresponding macro available for it...other situations
    # are avoided by 'continue' statements above which resume the loop.

    sequence = apps[app_index].macros[key_number][2]
    if pressed:
        # 'sequence' is an arbitrary-length list, each item is one of:
        # Positive integer (e.g. Keycode.KEYPAD_MINUS): key pressed
        # Negative integer: (absolute value) key released
        # Float (e.g. 0.25): delay in seconds
        # String (e.g. "Foo"): corresponding keys pressed & released
        # List []: one or more Consumer Control codes (can also do float delay)
        # Dict {}: mouse buttons/motion (might extend in future)
        if key_number < 12: # No pixel for encoder button
            macropad.pixels[key_number] = 0xFFFFFF
            macropad.pixels.show()
        for item in sequence:
            if isinstance(item, int):
                if item >= 0:
                    macropad.keyboard.press(item)
                else:
                    macropad.keyboard.release(-item)
            elif isinstance(item, float):
                time.sleep(item)
            elif isinstance(item, str):
                macropad.keyboard_layout.write(item)
            elif isinstance(item, list):
                for code in item:
                    if isinstance(code, int):
                        macropad.consumer_control.release()
                        macropad.consumer_control.press(code)
                    if isinstance(code, float):
                        time.sleep(code)
            elif isinstance(item, dict):
                if 'buttons' in item:
                    if item['buttons'] >= 0:
                        macropad.mouse.press(item['buttons'])
                    else:
                        macropad.mouse.release(-item['buttons'])
                macropad.mouse.move(item['x'] if 'x' in item else 0,
                                    item['y'] if 'y' in item else 0,
                                    item['wheel'] if 'wheel' in item else 0)
                if 'tone' in item:
                    if item['tone'] > 0:
                        macropad.stop_tone()
                        macropad.start_tone(item['tone'])
                    else:
                        macropad.stop_tone()
                elif 'play' in item:
                    macropad.play_file(item['play'])
    else:
        # Release any still-pressed keys, consumer codes, mouse buttons
        # Keys and mouse buttons are individually released this way (rather
        # than release_all()) because pad supports multi-key rollover, e.g.
        # could have a meta key or right-mouse held down by one macro and
        # press/release keys/buttons with others. Navigate popups, etc.
        for item in sequence:
            if isinstance(item, int):
                if item >= 0:
                    macropad.keyboard.release(item)
            elif isinstance(item, dict):
                if 'buttons' in item:
                    if item['buttons'] >= 0:
                        macropad.mouse.release(item['buttons'])
                elif 'tone' in item:
                    macropad.stop_tone()
        macropad.consumer_control.release()
        if key_number < 12: # No pixel for encoder button
            macropad.pixels[key_number] = apps[app_index].macros[key_number][0]
            macropad.pixels.show()

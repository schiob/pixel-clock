# Metro Matrix Clock
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield

import time
import board
import displayio
import terminalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

BLINK = True
DEBUG = False

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
print("    Metro Minimal Clock")
print("Time will be set for {}".format(secrets["timezone"]))

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=board.NEOPIXEL, debug=False)

# --- Drawing setup ---
group = displayio.Group(max_size=5)  # Create a Group
color = displayio.Palette(4)  # Create a color palette
color[0] = 0x000000  # black background
color[1] = 0x0085FF  # blue-green
color[2] = 0xCC4000  # amber
color[3] = 0x85FF00  # greenish

# menu
bitmap_file = open("/menu.bmp", "rb")
# Setup the file as the bitmap data source
bitmap_menu = displayio.OnDiskBitmap(bitmap_file)

# Create a TileGrid to hold the bitmap
tile_grid_menu = displayio.TileGrid(bitmap_menu,
                            pixel_shader=displayio.ColorConverter(),
                            width = 1,
                            height = 1,
                            tile_width = 10,
                            tile_height = 7)

# Add the TileGrid to the Group
group.append(tile_grid_menu)

# Create a TileGrid using the Bitmap and Palette
display.show(group)

if not DEBUG:
    font = bitmap_font.load_font("/RetroGaming-11.bdf")
else:
    font = terminalio.FONT

clock_label = Label(font, max_glyphs=8)
youtube_label = Label(font, max_glyphs=8)
youtube_label.text = "Hola"
bbx, bby, bbwidth, bbh = clock_label.bounding_box
youtube_label.x = round(display.width / 2 - bbwidth / 2)
youtube_label.y = display.height // 2

labels = [clock_label, youtube_label]

def update_time(*, hours=None, minutes=None, show_colon=False):
    now = time.localtime()  # Get the time values we need
    if hours is None:
        hours = now[3]
    if hours >= 18 or hours < 6:  # evening hours to morning
        clock_label.color = color[1]
    else:
        clock_label.color = color[3]  # daylight hours
    if hours > 12:  # Handle times later than 12:59
        hours -= 12
    elif not hours:  # Handle times between 0:00 and 0:59
        hours = 12

    if minutes is None:
        minutes = now[4]

    seconds = now[5]

    if BLINK:
        colon = ":" if show_colon or now[5] % 2 else " "
    else:
        colon = ":"

    clock_label.text = "{hours}{colon}{minutes:02d}{colon}{seconds:02d}".format(
        hours=hours, minutes=minutes, colon=colon, seconds=seconds
    )
    bbx, bby, bbwidth, bbh = clock_label.bounding_box
    # Center the label
    clock_label.x = round(display.width / 2 - bbwidth / 2)
    clock_label.y = display.height // 2
    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(bbx, bby, bbwidth, bbh))
        print("Label x: {} y: {}".format(clock_label.x, clock_label.y))


last_check = None
update_time(show_colon=True)  # Display whatever time is on the board
group.append(clock_label)  # add the clock label to the group

# Botones
button_down = DigitalInOut(board.BUTTON_DOWN)
button_down.switch_to_input(pull=Pull.UP)

while True:
    if last_check is None or time.monotonic() > last_check + 3600:
        try:
            update_time(
                show_colon=True
            )  # Make sure a colon is displayed while updating
            network.get_local_time()  # Synchronize Board's clock to Internet
            last_check = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)

    update_time()
    print(group[-1].text)
    if not button_down.value:
        if tile_grid_menu[0] == 1:
            tile_grid_menu[0] = 0
            group.pop()
            group.append(labels[0])
        else:
            tile_grid_menu[0] = 1
            group.pop()
            group.append(labels[1])

    time.sleep(.2)

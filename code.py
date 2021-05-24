# Metro Matrix Clock
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield

import time
import board
import displayio
import terminalio
from clock import ClockView
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

font = bitmap_font.load_font("/RetroGaming-11.bdf")

my_clock = ClockView(color, font, display)

youtube_label = Label(font, max_glyphs=8)
youtube_label.text = "Hola"
bbx, bby, bbwidth, bbh = youtube_label.bounding_box
youtube_label.x = round(display.width / 2 - bbwidth / 2)
youtube_label.y = display.height // 2

labels = [my_clock.clock_label, youtube_label]

last_check = None
my_clock.update_time(show_colon=True)  # Display whatever time is on the board
group.append(labels[0])  # add the clock label to the group

# Botones
button_down = DigitalInOut(board.BUTTON_DOWN)
button_down.switch_to_input(pull=Pull.UP)

while True:
    if last_check is None or time.monotonic() > last_check + 3600:
        try:
            my_clock.update_time(
                show_colon=True
            )  # Make sure a colon is displayed while updating
            network.get_local_time()  # Synchronize Board's clock to Internet
            last_check = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)

    my_clock.update_time()
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

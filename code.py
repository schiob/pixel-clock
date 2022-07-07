# Metro Matrix Clock
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield

import time
import board
import busio
import displayio
import terminalio
from clock import ClockView
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

adafruit_requests.set_socket(socket, esp)

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
network = Network(status_neopixel=board.NEOPIXEL, debug=False, external_spi=spi, esp=esp)

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

def get_subs(api_key):
    response = adafruit_requests.get("https://youtube.googleapis.com/youtube/v3/channels?part=statistics&id=UCjhbs3YjA7CPUw0-Dgb3f2A&key={}".format(api_key))

    json_youtube = response.json()
    print(json_youtube["items"][0]["statistics"]["subscriberCount"])

    return json_youtube["items"][0]["statistics"]["subscriberCount"]

# get_subs(secrets["youtube-key"])
youtube_label = Label(font, max_glyphs=8)
youtube_label.text = "Hola"
bbx, bby, bbwidth, bbh = youtube_label.bounding_box
youtube_label.x = round(display.width / 2 - bbwidth / 2)
youtube_label.y = display.height // 2

labels = [my_clock.clock_label, youtube_label]

last_check = None
my_clock.update_time(show_colon=True)  # Display whatever time is on the board
group.append(labels[0])  # add the clock label to the group
last_check_view = None

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
            youtube_label.text = get_subs(secrets["youtube-key"])
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
    
    if last_check_view is None or time.monotonic() > last_check_view + 10:
        last_check_view = time.monotonic()
        if tile_grid_menu[0] == 1:
            tile_grid_menu[0] = 0
            group.pop()
            group.append(labels[0])
        else:
            tile_grid_menu[0] = 1
            group.pop()
            group.append(labels[1])

    time.sleep(.2)

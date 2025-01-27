import time
import displayio
import board
import busio
from digitalio import DigitalInOut

import adafruit_connection_manager
import adafruit_requests
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_minimqtt.adafruit_minimqtt as MQTT

from secrets import secrets

# Import our views and ViewManager
from view_manager import ViewManager
from clock import ClockView
from home_assistant import HomeAssistantView

# -------------------------
# 1) WiFi + Hardware Setup
# -------------------------
if secrets == {"ssid": None, "password": None}:
    raise RuntimeError(
        "WiFi secrets are not set up. Please add them to settings.toml or secrets.py.")

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

if "SCK1" in dir(board):
    spi = busio.SPI(board.SCK1, board.MOSI1, board.MISO1)
else:
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)

print("Connecting to WiFi...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except OSError as e:
        print("Could not connect to AP, retrying:", e)
        continue
print("Connected to:", esp.ap_info.ssid)
print("My IP address is", esp.ipv4_address)

matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, esp=esp)
display = matrixportal.display

# Set up the palette/colors
COLOR_BLACK = 0x000000
COLOR_BLUE_GREEN = 0x0085FF
COLOR_AMBER = 0xCC4000
COLOR_GREENISH = 0x85FF00

PALETTE_SIZE = 4
palette = displayio.Palette(PALETTE_SIZE)
palette[0] = COLOR_BLACK       # Fondo negro
palette[1] = COLOR_BLUE_GREEN  # Azul-verde
palette[2] = COLOR_AMBER       # Ámbar
palette[3] = COLOR_GREENISH    # Verdoso

# Load font
FONT_PATH = "/RetroGaming-11.bdf"
font = bitmap_font.load_font(FONT_PATH)
font.load_glyphs(
    b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()-_=+[]{}|;:",.<>/?`~ '
)

# Clear anything from the display root group
display.root_group = displayio.Group()

# MQTT CLIENT
mqtt_broker = "192.168.0.22"
mqtt_port = 1883

mqtt_client = MQTT.MQTT(
    broker=mqtt_broker,
    port=mqtt_port,
    socket_pool=pool,
)

# -------------------------------------
# 2) Create our Views and ViewManager
# -------------------------------------
clock_view = ClockView(palette, font, display)
homeassistant_view = HomeAssistantView(
    palette, font, display, mqtt_client, "youtube")

manager = ViewManager(display)
manager.add_view(clock_view)
manager.add_view(homeassistant_view)

# Show the first view (clock)
manager.set_view(0)

# ---------------------
# 3) Main Loop
# ---------------------
# variable para refrescar tiempo NTP
ntp_refresh_time = None

# variable para cambiar de vista
view_switch_time = None

while True:
    # 1) Actualizar hora si pasan 900 seg
    if (not ntp_refresh_time) or ((time.monotonic() - ntp_refresh_time) > 900):
        try:
            print("Obtaining time from Adafruit IO server...")
            matrixportal.get_local_time()
            ntp_refresh_time = time.monotonic()
        except RuntimeError as e:
            print("Unable to obtain time, retrying -", e)
            continue

    # 2) Actualizar la vista actual
    manager.update()

    # 3) Procesar MQTT
    mqtt_client.loop()

    # 4) Cambiar de vista cada 10 segundos
    if (not view_switch_time) or ((time.monotonic() - view_switch_time) > 10):
        manager.next_view()
        # Reiniciamos el tiempo de cambio para que se cumplan
        # otros 10 segundos antes de cambiar de nuevo
        view_switch_time = time.monotonic()

    time.sleep(0.2)

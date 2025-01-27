import time
import board
import busio
import displayio
import terminalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_matrixportal.matrix import Matrix
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests

from clock import ClockView  # Asegúrate de que este módulo esté actualizado

# Importa el administrador de conexiones (asegúrate de tener este módulo)
import adafruit_connection_manager

# ----------------------------
# Constantes y Configuraciones
# ----------------------------

# Colores de la paleta
COLOR_BLACK = 0x000000
COLOR_BLUE_GREEN = 0x0085FF
COLOR_AMBER = 0xCC4000
COLOR_GREENISH = 0x85FF00

PALETTE_SIZE = 4

MENU_BITMAP_PATH = "/menu.bmp"
FONT_PATH = "/RetroGaming-11.bdf"

YOUTUBE_CHANNEL_ID = "UCjhbs3YjA7CPUw0-Dgb3f2A"  # Reemplaza con el ID de tu canal
UPDATE_INTERVAL = 3600  # Intervalo de actualización en segundos
VIEW_UPDATE_INTERVAL = 10  # Intervalo de actualización de vista en segundos
SLEEP_DURATION = 0.2  # Duración de la pausa en el bucle principal

# ----------------------------
# Inicialización de Hardware
# ----------------------------


def initialize_esp32_spi(secrets):
    """Inicializa el ESP32 SPI para la conectividad WiFi."""
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    esp = adafruit_esp32spi.ESP_SPIcontrol(
        spi, esp32_cs, esp32_ready, esp32_reset)

    if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
        print("ESP32 found and in idle mode")

    print("Firmware vers.", esp.firmware_version)
    print("MAC addr:", ":".join("%02X" % byte for byte in esp.MAC_address))

    for ap in esp.scan_networks():
        print("\t%-23s RSSI: %d" % (ap.ssid, ap.rssi))

    print("Connecting to AP...")
    while not esp.is_connected:
        try:
            esp.connect_AP(secrets["ssid"], secrets["password"])
        except OSError as e:
            print("could not connect to AP, retrying: ", e)
            continue
    print("Connected to", esp.ap_info.ssid, "\tRSSI:", esp.ap_info.rssi)
    print("My IP address is", esp.ipv4_address)

    return esp, spi


def initialize_network(spi, esp):
    """Inicializa la red utilizando MatrixPortal Network."""
    network = MatrixPortal(
        status_neopixel=board.NEOPIXEL,
        debug=True,
        esp=esp
    )
    return network


def initialize_display():
    """Inicializa la matriz de visualización."""
    matrix = Matrix()
    display = matrix.display
    return display


def initialize_palette():
    """Crea y retorna una paleta de colores."""
    palette = displayio.Palette(PALETTE_SIZE)
    palette[0] = COLOR_BLACK       # Fondo negro
    palette[1] = COLOR_BLUE_GREEN  # Azul-verde
    palette[2] = COLOR_AMBER        # Ámbar
    palette[3] = COLOR_GREENISH     # Verdoso
    return palette


def load_bitmap(palette):
    """Carga el bitmap del menú o crea uno por defecto si falla."""
    try:
        with open(MENU_BITMAP_PATH, "rb") as bitmap_file:
            bitmap_menu = displayio.OnDiskBitmap(bitmap_file)
    except OSError:
        print(f"No se pudo abrir {
              MENU_BITMAP_PATH}. Usando bitmap por defecto.")
        # Bitmap por defecto si falla la carga
        bitmap_menu = displayio.Bitmap(10, 7, 1)

    tile_grid_menu = displayio.TileGrid(
        bitmap_menu,
        pixel_shader=palette,
        width=1,
        height=1,
        tile_width=10,
        tile_height=7
    )
    return tile_grid_menu


def load_font():
    """Carga y retorna la fuente de texto."""
    font = bitmap_font.load_font(FONT_PATH)
    font.load_glyphs(
        b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()-_=+[]{}|;:",.<>/?`~ '
    )
    return font


def initialize_youtube_label(font, palette, display):
    """Inicializa la etiqueta de YouTube."""
    youtube_label = Label(
        font,
        color=palette[1],  # Azul-verde
        text="Cargando..."
    )
    youtube_label.anchor_point = (0.5, 0.5)
    youtube_label.anchored_position = (display.width // 2, display.height // 2)
    return youtube_label


def initialize_buttons():
    """Inicializa los botones."""
    button_down = DigitalInOut(board.BUTTON_DOWN)
    button_down.direction = Direction.INPUT
    button_down.pull = Pull.UP
    return button_down

# ----------------------------
# Clase Principal
# ----------------------------


class MetroMatrixClock:
    def __init__(self, secrets):
        """Inicializa todos los componentes del reloj."""
        # Inicializar ESP32 SPI
        self.esp, self.spi = initialize_esp32_spi(secrets)

        # Inicializar la red
        self.network = initialize_network(self.spi, self.esp)

        # Inicializar la visualización
        self.display = initialize_display()

        # Inicializar la paleta de colores
        self.palette = initialize_palette()

        # Crear el grupo de display y añadir el menú
        self.group = displayio.Group()
        self.tile_grid_menu = load_bitmap(self.palette)
        self.group.append(self.tile_grid_menu)
        self.display.root_group = self.group

        # Cargar la fuente de texto
        self.font = load_font()

        # Inicializar el reloj
        self.clock = ClockView(self.palette, self.font, self.display)

        # Inicializar la etiqueta de YouTube
        self.youtube_label = initialize_youtube_label(
            self.font, self.palette, self.display)
        self.labels = [self.clock.clock_label, self.youtube_label]
        # Añadir la etiqueta del reloj al grupo
        self.group.append(self.labels[0])

        # Inicializar variables de control
        self.last_check = None
        self.last_check_view = None

        # Inicializar botones
        self.button_down = initialize_buttons()

    def get_subs(self, api_key, channel_id=YOUTUBE_CHANNEL_ID):
        """
        Obtiene el número de suscriptores del canal de YouTube especificado.

        Args:
            api_key (str): Clave API de YouTube.
            channel_id (str): ID del canal de YouTube.

        Returns:
            str: Número de suscriptores como cadena de texto.
        """
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=statistics&id={
            channel_id}&key={api_key}"
        response = self.requests.get(url)
        json_youtube = response.json()
        subscriber_count = json_youtube["items"][0]["statistics"]["subscriberCount"]
        print(f"Suscriptores: {subscriber_count}")
        return subscriber_count

    def update_network_time_and_subs(self, api_key):
        """Actualiza la hora de la red y el número de suscriptores de YouTube."""
        try:
            # Asegurar que se muestre el colon al actualizar
            self.clock.update_time(show_colon=True)
            self.network.get_local_time()
            self.last_check = time.monotonic()
            # self.youtube_label.text = self.get_subs(api_key)
        except RuntimeError as e:
            print("Ocurrió un error al actualizar la red o YouTube, reintentando! -", e)

    def toggle_display_label(self):
        """Alterna entre mostrar la etiqueta del reloj y la de YouTube."""
        if self.tile_grid_menu[0] == 1:
            self.tile_grid_menu[0] = 0
            self.group.pop()  # Remover la última etiqueta
            self.group.append(self.labels[0])  # Añadir la etiqueta del reloj
        else:
            self.tile_grid_menu[0] = 1
            self.group.pop()
            self.group.append(self.labels[1])  # Añadir la etiqueta de YouTube

    def run(self, secrets):
        """Ejecuta el bucle principal del reloj."""
        print("    Metro Minimal Clock")
        print(f"Time will be set for {secrets['timezone']}")

        while True:
            current_time = time.monotonic()

            # Actualización de tiempo y suscriptores cada UPDATE_INTERVAL segundos
            if self.last_check is None or current_time > self.last_check + UPDATE_INTERVAL:
                self.update_network_time_and_subs(secrets["youtube-key"])

            # Actualiza la visualización del reloj
            self.clock.update_time()

            # Manejo de botón para alternar entre etiquetas
            if not self.button_down.value:
                self.toggle_display_label()

            # Actualización periódica de la vista cada VIEW_UPDATE_INTERVAL segundos
            if self.last_check_view is None or current_time > self.last_check_view + VIEW_UPDATE_INTERVAL:
                self.last_check_view = current_time
                self.toggle_display_label()

            time.sleep(SLEEP_DURATION)

# ----------------------------
# Función Principal
# ----------------------------


def main():
    """Función principal para iniciar el reloj."""
    # Obtener detalles de WiFi desde el archivo secrets.py
    try:
        from secrets import secrets
    except ImportError:
        print("WiFi secrets are kept in secrets.py, please add them there!")
        raise

    # Inicializar y ejecutar el reloj
    metro_clock = MetroMatrixClock(secrets)
    metro_clock.run(secrets)

# ----------------------------
# Punto de Entrada
# ----------------------------


if __name__ == "__main__":
    main()

import displayio
import json
from adafruit_display_text import label
from base_view import BaseView
import adafruit_minimqtt.adafruit_minimqtt as MQTT


class HomeAssistantView(BaseView):
    def __init__(self, palette, font, display, mqtt_client, topic):
        super().__init__(palette, font, display)

        self.mqtt_client = mqtt_client
        self.topic = topic
        self.current_value = "--"

        # Label para mostrar el valor recibido de Home Assistant
        self.value_label = label.Label(
            font,
            text="--",
            color=0xFFFF00
        )
        self.value_label.x = 2
        self.value_label.y = 12
        self.group.append(self.value_label)

        # Configurar callbacks de MQTT
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_connect = self.connected
        self.mqtt_client.on_disconnect = self.disconnected

        self.mqtt_client.connect()

    def connected(self, client, userdata, flags, rc):
        # This function will be called when the client is connected
        # successfully to the broker.
        print(f"Connected to MQTT broker! Listening for topic changes on {
              self.topic}")
        # Subscribe to all changes on the default_topic feed.
        client.subscribe(self.topic)

    def disconnected(self, client, userdata, rc):
        # This method is called when the client is disconnected
        print("Disconnected from MQTT Broker!")

    def on_mqtt_message(self, client, topic, payload):
        """
        Este callback se llama cuando llega un mensaje al topic suscrito.
        Aquí extraemos el valor y actualizamos la label.
        """
        try:
            # Si el payload viene en formato JSON, se parsea.
            # O si viene como simple string, lo asignas directo.
            data = json.loads(payload)
            # Ajusta según cómo publiques los datos desde HA
            new_value = data.get("state", "--")
            self.current_value = new_value
            self.value_label.text = f"{new_value}"
        except Exception as e:
            print("Error parseando payload MQTT:", e)

    def update(self):
        """
        Se llama en cada iteración del bucle principal.
        Si usas MQTT 'loop()' manual, lo podrías poner aquí.
        """
        # A veces se usa mqtt_client.loop() para procesar mensajes.
        # Depende de cómo configures tu MQTT client.
        # self.mqtt_client.loop()

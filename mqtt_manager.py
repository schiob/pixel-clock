import json
import adafruit_minimqtt.adafruit_minimqtt as MQTT


class MqttManager:
    """
    Maneja la conexión MQTT y el almacenamiento de datos para múltiples topics.
    """

    def __init__(self, broker, port, pool, keep_alive=60):
        self.broker = broker
        self.port = port
        self.keep_alive = keep_alive

        # Este dict almacenará el último payload de cada topic
        # clave: topic, valor: lo que se haya recibido
        self.topic_data = {}

        # Creamos el cliente MQTT de Adafruit MiniMQTT
        self.mqtt_client = MQTT.MQTT(
            broker=self.broker,
            port=self.port,
            socket_pool=pool,
            keep_alive=self.keep_alive
        )

        # Callback cuando llega un mensaje
        self.mqtt_client.on_message = self._message_callback

        # Podemos almacenar una referencia al ViewManager opcionalmente
        self.view_manager = None

    def set_view_manager(self, view_manager):
        """
        Para que el MqttManager pueda cambiar la vista activa si
        recibe un mensaje con un "comando" de cambio de vista.
        """
        self.view_manager = view_manager

    def connect(self):
        print("Conectando a MQTT...")
        self.mqtt_client.connect()
        print("Conectado a MQTT broker:", self.broker)

    def subscribe(self, topic):
        """Suscribe a un topic dado."""
        print("Suscribiendo a topic:", topic)
        self.mqtt_client.subscribe(topic)

    def loop(self):
        """Se llama periódicamente en el bucle principal."""
        self.mqtt_client.loop()

    def _message_callback(self, client, topic, payload):
        """
        Maneja los mensajes recibidos de MQTT.
        - Almacena el payload en self.topic_data[topic].
        - Si es un topic especial para cambiar vistas, lo procesa.
        """
        print("Mensaje MQTT recibido ->", topic, payload)

        # Convertimos a string o dict (si viene en JSON)
        # Ajusta según tu formato de datos
        data_str = payload
        try:
            data_json = json.loads(payload)  # si es JSON
        except ValueError:
            data_json = None

        # Guardamos
        self.topic_data[topic] = data_json if data_json else data_str

        # (Opcional) Si hay un topic especial para cambiar vistas, por ejemplo:
        #    "homeassistant/view" con payload = "0" o "clock" o "weather"
        if topic == "matrix/view" and self.view_manager:
            # Ejemplo 1: si en el payload viene un índice de vista
            try:
                new_view_index = int(data_str)
                self.view_manager.set_view(new_view_index)
            except ValueError:
                print("No se pudo convertir payload a int para cambiar de vista.")
            # Ejemplo 2: si en el payload viene un nombre de vista y mapeas texto->índice
            #   ...
            #   self.view_manager.set_view( some_index )

    def get_data(self, topic):
        """
        Devuelve el último payload almacenado para 'topic'.
        """
        return self.topic_data.get(topic, None)

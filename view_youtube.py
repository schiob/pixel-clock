from adafruit_display_text import label
from base_view import BaseView


class YoutubeView(BaseView):
    def __init__(self, palette, font, display, mqtt_manager, topic):
        super().__init__(palette, font, display)

        self.mqtt_manager = mqtt_manager
        self.topic = topic
        self.mqtt_manager.subscribe(topic)

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

    def update(self):
        """
        Se llama cada vez en el bucle principal. 
        Pedimos al mqtt_manager la data más reciente y la mostramos.
        """
        data = self.mqtt_manager.get_data(self.topic)
        if data is None:
            text_val = "--"
        else:
            # data podría ser un dict si venía en JSON, o un string
            # Ajustar según tu caso
            if isinstance(data, dict):
                # Asumimos que hay un campo 'state'
                text_val = data.get("state", "--")
            else:
                text_val = data

        self.value_label.text = f"{text_val}"

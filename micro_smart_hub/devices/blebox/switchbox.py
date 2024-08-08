from micro_smart_hub.device import IoTSwitch
from micro_smart_hub.registry import register_class
import requests


@register_class
class SwitchBox(IoTSwitch):
    def __init__(self, definition={}) -> None:
        super().__init__(definition)
        self.url = self.definition.get("url", "127.0.0.1")
        self.info = {}
        self.relays = []

    def load_info(self):
        response = requests.get(url=self.url + "/info")
        self.info = response.json().get('device', {})

    def load_state(self):
        response = requests.get(url=self.url + "/state")
        self.relays = response.json().get('relays', [])

    @property
    def on(self):
        if len(self.relays):
            self._on = self.relays[0]['state']
        return self._on

    @on.setter
    def on(self, value):
        self._on = value
        if len(self.relays):
            self.relays[0]['state'] = self._on
        requests.post(self.url + f"/s/{value}")

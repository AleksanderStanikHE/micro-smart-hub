import threading
import time
from enum import Enum
from micro_registry.registry import register_class
from micro_registry.component import MicroComponent


class DeviceState(Enum):
    CONNECTED = "Connected"
    NOT_CONNECTED = "Not Connected"
    ERROR = "Error"


class MicroDevice(MicroComponent):
    def __init__(self,
                 name: str = '',
                 parent=None,
                 device_type: str = '',
                 location: str = '',
                 interval: float = 1.0,
                 **kwargs) -> None:
        super().__init__(name, parent)
        self.device_type = device_type
        self.location = location
        self.interval = interval
        self.configuration = None
        self.state = DeviceState.NOT_CONNECTED
        self.pooling_counter = 0
        self.reset()

    def __del__(self):
        self.stop()

    def reset(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start the polling process in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Stop the polling process."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def _run(self):
        """Run the polling loop."""
        while self.running:
            try:
                if not self.configuration:
                    self.load_info()
                self.load_state()
                self.state = DeviceState.CONNECTED
            except Exception:
                self.configuration = None
                if self.state != DeviceState.NOT_CONNECTED:
                    self.state = DeviceState.ERROR
            time.sleep(self.interval)
            self.pooling_counter += 1

    def load_info(self):
        pass

    def load_state(self):
        pass


@register_class
class MicroSwitch(MicroDevice):
    def __init__(self, on: int = 0, **kwargs) -> None:
        super().__init__(device_type='switch', **kwargs)
        self._on = on

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = value


@register_class
class MicroLight(MicroDevice):
    def __init__(self, brightness: int = 100, **kwargs):
        super().__init__(device_type='light', **kwargs)
        self._brightness = brightness

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value


@register_class
class MicroThermostat(MicroDevice):
    def __init__(self, temperature: float = 20.0, **kwargs):
        super().__init__(device_type='thermostat', **kwargs)
        self._temperature = temperature

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        self._temperature = value

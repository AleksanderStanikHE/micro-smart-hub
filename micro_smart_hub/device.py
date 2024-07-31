import threading
import time
from enum import Enum


class DeviceState(Enum):
    CONNECTED = "Connected"
    NOT_CONNECTED = "Not Connected"
    ERROR = "Error"


class MicroDevice():
    def __init__(self, definition) -> None:
        if not definition:
            definition = {}
        self.definition = definition
        self.configuration = None
        self.state = DeviceState.NOT_CONNECTED
        self.pooling_counter = 0
        self.reset()

    def __del__(self):
        self.stop()

    def reset(self):
        self.interval = self.definition.get("interval", 1.0)
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


class IoTSwitch(MicroDevice):
    def __init__(self, definition={}) -> None:
        super().__init__(definition)
        self._on = 0

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = value

import abc
from typing import List
from micro_smart_hub.device import MicroDevice, IoTSwitch


class Automation(abc.ABC):
    def __init__(self, definition={}) -> None:
        self.definition = definition
        self.devices: List[MicroDevice] = None

    def run(self, action, parameters, devices) -> None:
        for device in devices:
            if isinstance(action, bool):
                if isinstance(device, IoTSwitch):
                    if action:
                        setattr(device, 'on', 1)
                    else:
                        setattr(device, 'on', 0)
                else:
                    print("Device should be of type 'IoTSwitch'")

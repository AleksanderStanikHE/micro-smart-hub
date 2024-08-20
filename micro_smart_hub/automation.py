import abc
from typing import List
from datetime import datetime
from micro_smart_hub.device import MicroDevice, IoTSwitch
from micro_smart_hub.registry import register_class


@register_class
class Automation(abc.ABC):
    def __init__(self, definition={}) -> None:
        self.definition = definition
        self.devices: List[MicroDevice] = None
        self.last_run_time: datetime = None

    def run(self, action, parameters, devices, scheduler=None) -> None:
        for device in devices:
            if isinstance(action, bool):
                if isinstance(device, IoTSwitch):
                    if action:
                        setattr(device, 'on', 1)
                    else:
                        setattr(device, 'on', 0)
                else:
                    print("Device should be of type 'IoTSwitch'")

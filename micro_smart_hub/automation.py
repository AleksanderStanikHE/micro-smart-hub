from typing import List
from datetime import datetime
from micro_smart_hub.device import MicroDevice
from micro_registry.registry import register_class, instance_registry
from micro_registry.component import MicroComponent


@register_class
class Automation(MicroComponent):
    def __init__(self,
                 name: str = '',
                 parent=None,
                 action: str = '',
                 target_devices: List[str] = None,
                 **kwargs
                 ) -> None:
        super().__init__(name, parent)
        self.target_device_names = target_devices or []
        self.devices: List[MicroDevice] = []
        self.last_run_time: datetime = None
        self.action = action

    def prepare(self):
        super().prepare()
        # Resolve device references
        self.target_devices = []
        for device_name in self.target_device_names:
            device = instance_registry.get(device_name)
            if device:
                self.target_devices.append(device)
            else:
                print(f"Device '{device_name}' not found for automation '{self.name}'.")

    def start(self):
        super().start()
        print(f"Automation '{self.name}' is starting.")
        self.execute()

    def run(self, action, parameters, devices, scheduler=None) -> None:
        if isinstance(action, bool):
            self.action = 'on'
            self.value = action
        else:
            self.action = action
        self.parameters = parameters
        self.target_devices = devices
        self.scheduler = scheduler
        self.execute()

    def execute(self):
        # print(f"Executing automation '{self.name}' with action '{self.action}'.")
        for device in self.target_devices:
            # Get the attribute or method from the device
            action_attr = getattr(device, self.action, None)
            if action_attr is None:
                print(f"Device '{device.name}' does not have action '{self.action}'.")
                continue

            # Check if the action is a callable method
            if callable(action_attr):
                # Check if parameters are provided
                if hasattr(self, 'parameters') and isinstance(self.parameters, dict):
                    try:
                        # Call the method with parameters
                        action_attr(**self.parameters)
                    except Exception as e:
                        print(f"Error executing '{self.action}' on device '{device.name}': {e}")
                else:
                    try:
                        # Call the method without parameters
                        action_attr()
                    except Exception as e:
                        print(f"Error executing '{self.action}' on device '{device.name}': {e}")
            else:
                # If it's an attribute, set its value if 'value' is provided
                if hasattr(self, 'value'):
                    try:
                        setattr(device, self.action, self.value)
                        # print(f"Set '{self.action}' to '{self.value}' on device '{device.name}'.")
                    except Exception as e:
                        print(f"Error setting '{self.action}' on device '{device.name}': {e}")
                else:
                    print(f"No value provided to set for '{self.action}' on device '{device.name}'.")

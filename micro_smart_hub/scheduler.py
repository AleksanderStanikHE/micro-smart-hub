import yaml
from typing import Dict
from datetime import datetime
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroDevice

Automations: Dict[str, Automation] = {}
Devices: Dict[str, MicroDevice] = {}


class MicroScheduler(Automation):
    def __init__(self) -> None:
        self.schedule = {}

    def load_schedule(self, schedule_file: str):
        with open(schedule_file, 'r') as file:
            self.schedule = yaml.safe_load(file)

    def run(self) -> None:
        current_time = datetime.now()
        current_day = current_time.strftime('%A').lower()
        current_hour = current_time.hour

        for automation_name, automation_data in self.schedule.items():
            if automation_name in Automations:
                tasks = automation_data.get('schedule', {}).get(current_day, [])
                devices_names = automation_data.get('devices', {})
                devices = list()
                for device_name in devices_names:
                    devices.append(Devices.get(device_name, None))
                for task in tasks:
                    if task['hour'] == current_hour:
                        action = task['action']
                        parameters = task.get('parameters', {})
                        parameters["current_hour"] = current_hour
                        parameters["current_day"] = current_day
                        automation = Automations[automation_name]
                        self.execute_task(automation, action, parameters, devices)

    def execute_task(self, automation, action, parameters, devices):
        if isinstance(automation, Automation):
            automation.run(action, parameters, devices)

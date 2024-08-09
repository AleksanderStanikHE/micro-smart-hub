import yaml
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroDevice
from micro_smart_hub.registry import filter_instances_by_base_class


class MicroScheduler:
    def __init__(self) -> None:
        self.schedule = {}
        self.running = True
        self.executor = ThreadPoolExecutor()  # Executor for running synchronous tasks

    def load_schedule(self, schedule_file: str):
        with open(schedule_file, 'r') as file:
            self.schedule = yaml.safe_load(file)

    async def run(self) -> None:
        Automations = filter_instances_by_base_class(Automation)
        current_time = datetime.now()
        current_day = current_time.strftime('%A').lower()
        current_hour = current_time.hour

        # Gather tasks to be run at the current hour
        tasks = []
        for automation_name, automation_data in self.schedule.items():
            if automation_name in Automations:
                tasks.extend(self.schedule_tasks_for_hour(automation_name, automation_data, current_day, current_hour))

        # Execute all gathered tasks concurrently
        await asyncio.gather(*tasks)

    def schedule_tasks_for_hour(self, automation_name: str, automation_data: dict, current_day: str, current_hour: int):
        Devices = filter_instances_by_base_class(MicroDevice)
        Automations = filter_instances_by_base_class(Automation)
        tasks = []
        schedule_tasks = automation_data.get('schedule', {}).get(current_day, [])
        devices_names = automation_data.get('devices', {})
        devices = [Devices.get(device_name, None) for device_name in devices_names]

        for task in schedule_tasks:
            if task['hour'] == current_hour:
                action = task['action']
                parameters = task.get('parameters', {})
                parameters["current_hour"] = current_hour
                parameters["current_day"] = current_day
                automation = Automations[automation_name]
                # Add a coroutine task to the list
                tasks.append(self.execute_task(automation, action, parameters, devices))

        return tasks

    async def execute_task(self, automation, action, parameters, devices):
        if isinstance(automation, Automation):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                automation.run,  # This is the synchronous method
                action,          # Pass the arguments
                parameters,
                devices
            )

    def stop(self):
        """Stop the scheduler loop."""
        self.running = False


class SchedulerRunner:
    def __init__(self, scheduler: MicroScheduler):
        self.scheduler = scheduler
        self.loop_counter = 0
        self.running = True

    async def run_forever(self):
        """Run the scheduler in a continuous loop."""
        while self.running:
            await self.scheduler.run()

            # Wait a bit before the next check (e.g., every minute)
            await asyncio.sleep(0.1)  # Check every minute
            self.loop_counter += 1

    def stop(self):
        """Stop the scheduler loop."""
        self.running = False

import yaml
import asyncio
from datetime import datetime, timedelta
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
        """Load schedule from a YAML file."""
        try:
            with open(schedule_file, 'r') as file:
                self.schedule = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading schedule file: {e}")

    async def run(self) -> None:
        """Run scheduled tasks."""
        Automations = filter_instances_by_base_class(Automation)
        current_time = datetime.now()
        current_day = current_time.strftime('%A').lower()

        # Gather tasks to be run at the current time
        tasks = []
        for automation_name, automation_data in self.schedule.items():
            if automation_name in Automations:
                tasks.extend(self.schedule_tasks_for_time(automation_name, automation_data, current_day, current_time))

        # Execute all gathered tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)

    def schedule_tasks_for_time(self, automation_name: str, automation_data: dict, current_day: str, current_time: datetime):
        """Schedule tasks to be run at the current time."""
        Devices = filter_instances_by_base_class(MicroDevice)
        Automations = filter_instances_by_base_class(Automation)
        tasks = []
        current_hour = current_time.hour
        current_minute = current_time.minute
        schedule_tasks = automation_data.get('schedule', {}).get(current_day, [])
        devices_names = automation_data.get('devices', [])
        devices = [Devices.get(device_name, None) for device_name in devices_names]

        for task in schedule_tasks:
            task_hour, task_minute = self.parse_task_time(task['time'])
            task_time = current_time.replace(hour=task_hour, minute=task_minute, second=0, microsecond=0)
            if task_time <= current_time < task_time + timedelta(minutes=1):
                action = task['action']
                parameters = task.get('parameters', {})
                parameters["current_hour"] = current_hour
                parameters["current_minute"] = current_minute
                parameters["current_day"] = current_day
                automation = Automations[automation_name]
                # Add a coroutine task to the list
                tasks.append(self.execute_task(automation, action, parameters, devices))

        return tasks

    @staticmethod
    def parse_task_time(task_time):
        """Parse the task time, which could be an integer, float, or a 'HH:MM' string."""
        if isinstance(task_time, int):
            hour = task_time
            minute = 0
        elif isinstance(task_time, float):
            hour = int(task_time)
            # Calculate the minutes by taking the fractional part, multiplying by 100, and rounding to 2 decimal places
            minute = int(round((task_time - hour) * 100, 2))
        elif isinstance(task_time, str) and ':' in task_time:
            hour, minute = map(int, task_time.split(':'))
        else:
            raise ValueError(f"Invalid time format: {task_time}")

        # Check that hours are within the 0-23 range
        if not (0 <= hour < 24):
            raise ValueError(f"Hours out of range: {hour}")

        # Check that minutes are within the 0-59 range
        if not (0 <= minute < 60):
            raise ValueError(f"Minutes out of range: {minute}")

        return hour, minute

    async def execute_task(self, automation, action, parameters, devices):
        """Execute the scheduled automation task."""
        if isinstance(automation, Automation):
            loop = asyncio.get_event_loop()
            try:
                await loop.run_in_executor(
                    self.executor,
                    automation.run,  # This is the synchronous method
                    action,          # Pass the arguments
                    parameters,
                    devices
                )
            except Exception as e:
                print(f"Error executing task for {automation}: {e}")

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

            await asyncio.sleep(0.002)  # Check every minute
            self.loop_counter += 1

    def stop(self):
        """Stop the scheduler loop."""
        self.running = False

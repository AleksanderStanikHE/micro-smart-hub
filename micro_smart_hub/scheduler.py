import yaml
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroDevice
from micro_registry.registry import filter_instances_by_base_class, register_class
from micro_registry.component import MicroComponent


@register_class
class MicroScheduler(MicroComponent):
    def __init__(self, name: str = '', parent=None, schedule_file: str = None, **kwargs) -> None:
        super().__init__(name, parent)
        self.current_time = datetime.now()
        self.current_day_name = self.current_time.strftime('%A')
        self.time_to_next_action = None  # Time until the next scheduled action
        self.next_automation_name = None  # Name of the next automation
        self.next_action_info = None
        self.next_action = None  # Action of the next automation
        self.schedule = {}
        self.running = True
        self.executor = ThreadPoolExecutor()  # Executor for running synchronous tasks
        self.last_run_time = None  # Track the last time the scheduler was run
        self.load_schedule(schedule_file)

    def load_schedule(self, schedule_file: str):
        """Load schedule from a YAML file."""
        if not schedule_file:
            print("No schedule file provided or file name is empty.")
            self.schedule = {}
            return
        try:
            with open(schedule_file, 'r') as file:
                self.schedule = yaml.safe_load(file)
                print(f"Schedule loaded from '{schedule_file}'.")
        except FileNotFoundError:
            print(f"Schedule file '{schedule_file}' not found.")
            self.schedule = {}
        except Exception as e:
            print(f"Error loading schedule file: {e}")
            self.schedule = {}

    async def run(self) -> None:
        """Run scheduled tasks."""
        Automations = filter_instances_by_base_class(Automation)
        self.current_time = datetime.now()
        self.current_day_name = self.current_time.strftime('%A')
        current_time = datetime.now()
        current_day = current_time.strftime('%A').lower()

        # Calculate time to the next action and update next automation details
        self.time_to_next_action, self.next_automation_name, self.next_action = self.calculate_time_to_next_action(current_time)
        self.next_action_info = self.next_automation_name, self.next_action

        # Set the last run time to current time if it's the first run
        if self.last_run_time is None:
            self.last_run_time = current_time

        # Gather tasks to be run between the last run time and now
        tasks = []
        for automation_name, automation_data in self.schedule.items():
            if automation_name in Automations:
                tasks.extend(self.schedule_tasks_for_time_range(automation_name, automation_data, current_day, current_time))
                Automations[automation_name].last_time_run = datetime.now()

        # Execute all gathered tasks concurrently
        if tasks:
            await asyncio.gather(*tasks)

        # Update the last run time
        self.last_run_time = current_time

    def get_datetime_for_day(self, day_name, hour, minute) -> datetime:
        # Get the current date and time
        now = datetime.now()

        # Get the current day of the week (0 = Monday, 6 = Sunday)
        current_day_index = now.weekday()

        # Map the day name to the corresponding day index
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }

        # Get the target day index
        target_day_index = day_map[day_name.lower()]

        # Calculate the difference in days, assuming the target day is before or equal to today
        if target_day_index > current_day_index:
            day_difference = target_day_index - current_day_index - 7
        else:
            day_difference = target_day_index - current_day_index

        # Calculate the target date
        target_date = now + timedelta(days=day_difference)

        # Create the datetime object with the target date, hour, and minute
        target_datetime = datetime(target_date.year, target_date.month, target_date.day, hour, minute)

        return target_datetime

    def find_first_task_before(self, schedule_tasks: dict, current_time: datetime):
        last_time = None
        last_task = None
        for day_name, scheduled_tasks_per_day in schedule_tasks.items():
            for task in scheduled_tasks_per_day:
                task_hour, task_minute = self.parse_task_time(task['time'])
                if day_name == 'daily':
                    day_name = current_time.strftime('%A').lower()
                task_time = self.get_datetime_for_day(day_name, task_hour, task_minute)
                if task_time <= current_time:
                    if last_time is None:
                        last_time = task_time
                        last_task = task
                    if task_time > last_time:
                        last_time = task_time
                        last_task = task
        return last_task, last_time

    def schedule_tasks_for_time_range(self, automation_name: str, automation_data: dict, current_day: str, current_time: datetime):
        """Schedule tasks to be run between the start_time and end_time."""
        Devices = filter_instances_by_base_class(MicroDevice)
        Automations = filter_instances_by_base_class(Automation)
        automation = Automations[automation_name]
        tasks = []
        schedule_tasks = automation_data.get('schedule', {})
        devices_names = automation_data.get('devices', [])
        devices = [Devices.get(device_name, None) for device_name in devices_names]

        if schedule_tasks:
            last_task, last_time = self.find_first_task_before(schedule_tasks, current_time)
        else:
            last_task = automation_data
            last_time = current_time

        if automation.last_run_time != last_time:
            action = last_task.get('action', None)
            parameters = last_task.get('parameters', {})
            parameters["current_hour"] = last_time.hour
            parameters["current_minute"] = last_time.minute
            parameters["current_day"] = current_day
            # automation = Automations[automation_name]
            # Add a coroutine task to the list
            tasks.append(self.execute_task(automation, action, parameters, devices))

        return tasks

    def calculate_time_to_next_action(self, current_time: datetime):
        """Calculate the time until the next scheduled action, and get its automation name and action."""
        next_task_time = None
        next_automation_name = None
        next_action = None

        for automation_name, automation_data in self.schedule.items():
            schedule_tasks = automation_data.get('schedule', {})
            for day_name, tasks_per_day in schedule_tasks.items():
                for task in tasks_per_day:
                    task_hour, task_minute = self.parse_task_time(task['time'])
                    if day_name == 'daily':
                        day_name = current_time.strftime('%A').lower()
                    task_time = self.get_datetime_for_day(day_name, task_hour, task_minute)
                    if task_time > current_time:
                        if next_task_time is None or task_time < next_task_time:
                            next_task_time = task_time
                            next_automation_name = automation_name
                            next_action = task.get('action', None)

        if next_task_time:
            time_to_next_action = next_task_time - current_time
            return time_to_next_action, next_automation_name, next_action
        else:
            return None, None, None

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
                    devices,
                    self  # main scheduler instance
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

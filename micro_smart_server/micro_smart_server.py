import asyncio
import curses
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from micro_smart_hub.scheduler import MicroScheduler, MicroDevice, Automation
from micro_smart_hub.registry import load_modules_from_directory, load_instances_from_yaml, filter_instances_by_base_class

# Default directories and file names
DEFAULT_DEVICE_DIRS = ['.']
DEFAULT_AUTOMATION_DIRS = ['.']
DEFAULT_CONFIG_FILE = './config.yaml'
DEFAULT_SCHEDULE_FILE = './schedule.yaml'


def parse_time_string(time_str):
    """Parse the time string to return hours and minutes."""
    if isinstance(time_str, int):
        return time_str, 0  # Only hour is provided
    elif isinstance(time_str, float):
        hour = int(time_str)
        minute = int(round((time_str - hour) * 100))
        return hour, minute
    elif isinstance(time_str, str) and ':' in time_str:
        hour, minute = map(int, time_str.split(':'))
        return hour, minute
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def find_next_tasks(scheduler):
    """Find the next tasks to be executed."""
    current_time = datetime.now()
    current_day = current_time.strftime('%A').lower()
    next_task_time = None
    next_tasks = defaultdict(list)

    # Iterate over the schedule for the current day and the next day
    days_to_check = [current_day, (current_time + timedelta(days=1)).strftime('%A').lower()]

    for day_offset, day in enumerate(days_to_check):
        for automation_name, automation_data in scheduler.schedule.items():
            tasks = automation_data.get('schedule', {}).get(day, [])
            devices = automation_data.get('devices', [])
            for task in tasks:
                task_hour, task_minute = parse_time_string(task['time'])
                task_time = datetime.combine(
                    current_time.date(),
                    datetime.min.time()
                ) + timedelta(days=day_offset, hours=task_hour, minutes=task_minute)

                if task_time > current_time:
                    if next_task_time is None or task_time < next_task_time:
                        next_task_time = task_time
                        next_tasks.clear()
                        next_tasks[next_task_time].append((automation_name, task['action'], devices))
                    elif task_time == next_task_time:
                        next_tasks[next_task_time].append((automation_name, task['action'], devices))

    if next_task_time:
        time_to_next_task = (next_task_time - current_time).total_seconds()
    else:
        time_to_next_task = None

    return next_tasks[next_task_time], next_task_time, time_to_next_task


async def update_display(stdscr, scheduler):
    """Coroutine to update the display in an asynchronous loop."""

    while True:
        current_time = datetime.now()
        current_day_name = current_time.strftime('%A')

        stdscr.clear()
        stdscr.addstr(0, 0, "Micro Smart Hub Scheduler")
        stdscr.addstr(1, 0, "==========================")
        stdscr.addstr(2, 0, f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} ({current_day_name})")
        stdscr.addstr(3, 0, "Press Ctrl+C to stop the scheduler")

        # Find and display the next scheduled tasks with actions
        next_tasks, next_task_time, time_to_next_task = find_next_tasks(scheduler)
        stdscr.addstr(5, 0, "Next Tasks:")
        if next_tasks and next_task_time:
            for idx, (task, action, devices) in enumerate(next_tasks, start=6):
                if isinstance(action, bool):
                    action = "on" if action else "off"
                stdscr.addstr(idx, 0, f"- {task}: {action} -> {devices}")
            stdscr.addstr(idx + 1, 0, f"Scheduled Time: {next_task_time.strftime('%Y-%m-%d %H:%M:%S')}")
            stdscr.addstr(idx + 2, 0, f"Time to Trigger: {timedelta(seconds=int(time_to_next_task))}")
            next_section_start = idx + 4
        else:
            stdscr.addstr(6, 0, "No upcoming tasks for today.")
            next_section_start = 7

        # Display loaded automations
        stdscr.addstr(next_section_start, 0, "Currently loaded automations:")
        automations = scheduler.schedule.keys()
        automation_filtered_registry = filter_instances_by_base_class(Automation)
        for idx, automation_name in enumerate(automations, start=next_section_start + 1):
            automation = automation_filtered_registry.get(automation_name, None)
            if automation:
                if hasattr(automation, 'definition'):
                    stdscr.addstr(idx, 0, f"- {automation_name} : {automation.definition}")

        # Display loaded devices
        stdscr.addstr(idx + 2, 0, "Currently loaded devices:")
        devices_idx = idx + 3
        device_filtered_registry = filter_instances_by_base_class(MicroDevice)
        for device_name, device in device_filtered_registry.items():
            if hasattr(device, 'definition'):
                stdscr.addstr(devices_idx, 0, f"- {device_name} : {device.definition}")
                devices_idx += 1

        stdscr.refresh()
        await asyncio.sleep(1)  # Update every second for demo purposes


def run_scheduler(stdscr, args):
    """Function to run the asyncio event loop with curses."""
    curses.curs_set(0)  # Hide cursor

    # Load devices and automations from specified directories or defaults
    device_dirs = args.devices or DEFAULT_DEVICE_DIRS
    for device_dir in device_dirs:
        load_modules_from_directory(device_dir)

    automation_dirs = args.automations or DEFAULT_AUTOMATION_DIRS
    for automation_dir in automation_dirs:
        load_modules_from_directory(automation_dir)

    # Load devices from YAML file if provided
    config_yaml = args.config or DEFAULT_CONFIG_FILE
    load_instances_from_yaml(config_yaml)

    # Load the schedule file
    schedule_file = args.schedule or DEFAULT_SCHEDULE_FILE
    scheduler = MicroScheduler()
    scheduler.load_schedule(schedule_file)

    # Create an asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the asynchronous display update function
    try:
        loop.run_until_complete(update_display(stdscr, scheduler))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


def main():
    parser = argparse.ArgumentParser(description="Run the Micro Smart Hub scheduler.")
    parser.add_argument('-s', '--schedule', type=str, nargs='?', default=DEFAULT_SCHEDULE_FILE, help='Path to the schedule YAML file.')
    parser.add_argument('-d', '--devices', type=str, nargs='+', help='Directories containing device modules.')
    parser.add_argument('-a', '--automations', type=str, nargs='+', help='Directories containing automation modules.')
    parser.add_argument('-c', '--config', type=str, help='Path to the configuration YAML file.')

    args = parser.parse_args()

    # Use curses.wrapper to initialize curses and call run_scheduler
    curses.wrapper(run_scheduler, args)


if __name__ == "__main__":
    main()

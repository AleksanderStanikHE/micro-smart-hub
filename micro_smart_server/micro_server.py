import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


import asyncio
import curses
import argparse
from datetime import datetime, timedelta
from micro_smart_hub.scheduler import MicroScheduler
from micro_smart_hub.registry import load_modules_from_directory, load_instances_from_yaml

# Default directories and file names
DEFAULT_DEVICE_DIRS = ['.']
DEFAULT_AUTOMATION_DIRS = ['.']
DEFAULT_CONFIG_FILE = './config.yaml'
DEFAULT_SCHEDULE_FILE = './schedule.yaml'


def find_next_task(scheduler):
    """Find the next task to be executed."""
    current_time = datetime.now()
    current_day = current_time.strftime('%A').lower()
    next_task_time = None
    next_task_name = None

    # Iterate over the schedule to find the closest future task
    for automation_name, automation_data in scheduler.schedule.items():
        tasks = automation_data.get('schedule', {}).get(current_day, [])
        for task in tasks:
            task_time = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=task['hour'])
            if task_time > current_time:
                if next_task_time is None or task_time < next_task_time:
                    next_task_time = task_time
                    next_task_name = automation_name

    if next_task_time:
        time_to_next_task = (next_task_time - current_time).total_seconds()
    else:
        time_to_next_task = None

    return next_task_name, next_task_time, time_to_next_task


async def update_display(stdscr, scheduler):
    """Coroutine to update the display in an asynchronous loop."""
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Micro Smart Hub Scheduler")
        stdscr.addstr(1, 0, "==========================")
        stdscr.addstr(2, 0, f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        stdscr.addstr(3, 0, "Press Ctrl+C to stop the scheduler")

        # Display loaded automations
        stdscr.addstr(5, 0, "Currently loaded automations:")
        automations = scheduler.schedule.keys()
        for idx, automation in enumerate(automations, start=6):
            stdscr.addstr(idx, 0, f"- {automation}")

        # Find and display the next scheduled task
        next_task_name, next_task_time, time_to_next_task = find_next_task(scheduler)
        if next_task_name and next_task_time:
            stdscr.addstr(10, 0, f"Next Task: {next_task_name}")
            stdscr.addstr(11, 0, f"Scheduled Time: {next_task_time.strftime('%Y-%m-%d %H:%M:%S')}")
            stdscr.addstr(12, 0, f"Time to Trigger: {timedelta(seconds=int(time_to_next_task))}")
        else:
            stdscr.addstr(10, 0, "No upcoming tasks for today.")

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

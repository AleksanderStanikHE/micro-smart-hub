import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
import asyncio
import threading
import time
from unittest.mock import patch
from datetime import datetime, timedelta
from micro_smart_hub.scheduler import MicroScheduler, SchedulerRunner
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroSwitch
from micro_registry.registry import instance_registry


class TestMicroSchedulerRealScenario(unittest.TestCase):

    def setUp(self):
        instance_registry["FakeAutomation_1"] = Automation(name="FakeAutomation_1")
        instance_registry["FakeSwitch_1"] = MicroSwitch(name="FakeSwitch_1")

        self.scheduler = MicroScheduler(name="Scheduler")
        schedule_file_path = os.path.join(os.path.dirname(__file__), 'real_scenario_schedule.yaml')
        self.scheduler.load_schedule(schedule_file_path)
        self.runner = SchedulerRunner(self.scheduler)

        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.start()

    def tearDown(self):
        # Stop the scheduler thread after tests
        self.runner.stop()
        self.scheduler_thread.join()

    def run_scheduler(self):
        """Function to run the scheduler in a separate thread."""
        asyncio.run(self.runner.run_forever())

    @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
    def test_scheduler(self, mock_datetime):
        instance_registry["FakeSwitch_1"].on = 0
        mock_datetime.strftime = datetime.strftime

        # Simulate a day's worth of schedule checks
        start_time = datetime(2024, 7, 19, 0)

        on_time = start_time + timedelta(hours=6, minutes=0)
        off_time = start_time + timedelta(hours=18, minutes=45)
        # Check the scheduler for each hour in a simulated day
        for hour_offset in range(0, 24):  # Simulate a full day
            for minute_offset in range(0, 60):
                current_time = start_time + timedelta(hours=hour_offset, minutes=minute_offset)
                mock_datetime.now.return_value = current_time

                expected_state = False
                # Check the switch state based on the expected schedule
                if on_time <= current_time < off_time:
                    expected_state = True
                # Allow some time for the scheduler to process (this is where you might wait for real I/O in a real test)
                time.sleep(0.01)
                self.assertEqual(instance_registry["FakeSwitch_1"].on, expected_state, f"Hour = {hour_offset}:{minute_offset}")
                # print(instance_registry["FakeSwitch_1"].on, expected_state, f"Hour = {hour_offset}:{minute_offset}")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroSchedulerRealScenario('test_scheduler'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

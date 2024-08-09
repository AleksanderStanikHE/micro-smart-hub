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
from micro_smart_hub.device import IoTSwitch
from micro_smart_hub.registry import instance_registry


class TestMicroSchedulerRealScenario(unittest.TestCase):

    def setUp(self):
        instance_registry["FakeAutomation"] = Automation()
        instance_registry["FakeSwitch"] = IoTSwitch()

        self.scheduler = MicroScheduler()
        schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
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

    @patch('micro_smart_hub.scheduler.datetime')
    def test_scheduler(self, mock_datetime):
        mock_datetime.strftime = datetime.strftime

        # Simulate a day's worth of schedule checks
        start_time = datetime(2024, 7, 19, 6)

        # Check the scheduler for each hour in a simulated day
        for hour_offset in range(0, 24):  # Simulate a full day
            current_time = start_time + timedelta(hours=hour_offset)
            mock_datetime.now.return_value = current_time

            # Allow some time for the scheduler to process (this is where you might wait for real I/O in a real test)
            time.sleep(0.2)

            # Check the switch state based on the expected schedule
            expected_state = 1 if 6 <= current_time.hour < 18 else 0
            self.assertEqual(instance_registry["FakeSwitch"].on, expected_state, f"Hour = {hour_offset}")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroSchedulerRealScenario('test_scheduler'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

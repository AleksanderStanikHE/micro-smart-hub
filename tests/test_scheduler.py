import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from datetime import datetime
import time
from unittest.mock import patch
from micro_smart_hub.scheduler import MicroScheduler, Automations, Devices
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import IoTSwitch


class LazySwitch(IoTSwitch):
    def __init__(self, definition={}) -> None:
        super().__init__(definition)
        self._on = 0

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        time.sleep(2)
        self._on = value


class TestMicroScheduler(unittest.IsolatedAsyncioTestCase):

    def test_scheduler_init(self):
        scheduler = MicroScheduler()
        self.assertIsInstance(scheduler, MicroScheduler)

        self.assertIsInstance(Devices, dict)
        self.assertIsInstance(Automations, dict)
        self.assertIsInstance(scheduler.schedule, dict)

    @patch('micro_smart_hub.scheduler.datetime')
    async def test_scheduler(self, mock_datetime):
        mock_datetime.strftime = datetime.strftime

        scheduler = MicroScheduler()
        Automations["FakeAutomation"] = Automation()
        Devices["FakeSwitch"] = IoTSwitch()

        schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
        scheduler.load_schedule(schedule_file_path)

        self.assertTrue("FakeAutomation" in scheduler.schedule)
        fake_automation_schedule = scheduler.schedule["FakeAutomation"]["schedule"]
        self.assertTrue("monday" in fake_automation_schedule)
        self.assertTrue("wednesday" in fake_automation_schedule)
        self.assertTrue("friday" in fake_automation_schedule)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 6)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 7)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 8)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 18)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 19)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 20)
        await scheduler.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)

    @patch('micro_smart_hub.scheduler.datetime')
    async def test_scheduler_concurrent_execution(self, mock_datetime):
        mock_datetime.strftime = datetime.strftime

        scheduler = MicroScheduler()
        Automations["Irrigation"] = Automation()
        Automations["Garden_Lights"] = Automation()
        Automations["Front_Lights"] = Automation()
        Devices["Irrigation_Pump"] = LazySwitch()
        Devices["Front_Light"] = LazySwitch()
        Devices["Garden_Light"] = LazySwitch()

        schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
        scheduler.load_schedule(schedule_file_path)

        # Set the mock time to a point where both FakeAutomation and Irrigation should run
        mock_datetime.now.return_value = datetime(2024, 7, 22, 6)

        # Verify the switch state
        self.assertEqual(Devices["Irrigation_Pump"].on, 0)
        self.assertEqual(Devices["Front_Light"].on, 0)
        self.assertEqual(Devices["Garden_Light"].on, 0)

        # Measure the execution time of the scheduler
        start_time = time.time()
        await scheduler.run()
        elapsed_time = time.time() - start_time

        # Verify the switch state
        self.assertEqual(Devices["Irrigation_Pump"].on, 1)
        self.assertEqual(Devices["Front_Light"].on, 1)
        self.assertEqual(Devices["Garden_Light"].on, 1)

        # Assert that the elapsed time is within an acceptable range
        self.assertLess(elapsed_time, 3, "Scheduler run took too long")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroScheduler('test_scheduler_init'))
    suite.addTest(TestMicroScheduler('test_scheduler'))
    suite.addTest(TestMicroScheduler('test_scheduler_concurrent_execution'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

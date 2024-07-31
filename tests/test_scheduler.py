import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from datetime import datetime
from unittest.mock import patch
from micro_smart_hub.scheduler import MicroScheduler, Automations, Devices
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import IoTSwitch


class TestMicroScheduler(unittest.TestCase):

    def test_scheduler_init(self):
        smart_home = MicroScheduler()
        self.assertIsInstance(smart_home, MicroScheduler)

        self.assertIsInstance(Devices, dict)
        self.assertIsInstance(Automations, dict)
        self.assertIsInstance(smart_home.schedule, dict)

    @patch('micro_smart_hub.scheduler.datetime')
    def test_scheduler(self, mock_datetime):
        mock_datetime.strftime = datetime.strftime

        smart_home = MicroScheduler()
        Automations["FakeAutomation"] = Automation()
        Devices["FakeSwitch"] = IoTSwitch()

        schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
        smart_home.load_schedule(schedule_file_path)
        self.assertTrue("FakeAutomation" in smart_home.schedule)
        fake_automation_schedule = smart_home.schedule["FakeAutomation"]["schedule"]
        self.assertTrue("monday" in fake_automation_schedule)
        self.assertTrue("wednesday" in fake_automation_schedule)
        self.assertTrue("friday" in fake_automation_schedule)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 6)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 7)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 8)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 1)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 18)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 19)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)

        mock_datetime.now.return_value = datetime(2024, 7, 19, 20)
        smart_home.run()
        self.assertEqual(Devices["FakeSwitch"].on, 0)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroScheduler('test_scheduler_init'))
    suite.addTest(TestMicroScheduler('test_scheduler'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

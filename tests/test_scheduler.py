import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from datetime import datetime
import time
from unittest.mock import patch
from micro_smart_hub.scheduler import MicroScheduler
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroSwitch
from micro_registry.registry import instance_registry, class_registry


class LazySwitch(MicroSwitch):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._on = 0

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        time.sleep(2)
        self._on = value


# Use Python version to choose the appropriate test class
if sys.version_info >= (3, 8):

    class TestMicroScheduler(unittest.IsolatedAsyncioTestCase):

        def test_01_scheduler_init(self):
            instance_registry.clear()
            class_registry.clear()
            scheduler = MicroScheduler(name="Scheduler")
            self.assertIsInstance(scheduler, MicroScheduler)
            self.assertIsInstance(scheduler.schedule, dict)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        async def test_02_scheduler(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["FakeAutomation"] = Automation(name="FakeAutomation")
            instance_registry["FakeSwitch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            self.assertIn("FakeAutomation", scheduler.schedule)
            fake_automation_schedule = scheduler.schedule["FakeAutomation"]["schedule"]
            self.assertIn("monday", fake_automation_schedule)
            self.assertIn("wednesday", fake_automation_schedule)
            self.assertIn("friday", fake_automation_schedule)

            # Test different scheduled times
            times_to_test = [
                (datetime(2024, 7, 19, 6, 0), 1),
                (datetime(2024, 7, 19, 6, 15), 1),
                (datetime(2024, 7, 19, 18, 0), 1),
                (datetime(2024, 7, 19, 18, 30), 1),
                (datetime(2024, 7, 19, 18, 45), 0),
                (datetime(2024, 7, 19, 19, 0), 0),
            ]

            for mock_time, expected_on in times_to_test:
                mock_datetime.now.return_value = mock_time
                await scheduler.run()
                self.assertEqual(instance_registry["FakeSwitch"].on, expected_on)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        async def test_03_scheduler_concurrent_execution(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["Irrigation"] = Automation(name="Irrigation")
            instance_registry["Garden_Lights"] = Automation(name="Garden_Lights")
            instance_registry["Front_Lights"] = Automation(name="Front_Lights")
            instance_registry["Irrigation_Pump"] = LazySwitch(name="FakeSwitch")
            instance_registry["Front_Light"] = LazySwitch(name="FakeSwitch")
            instance_registry["Garden_Light"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Set the mock time to a point where all actions should run
            mock_datetime.now.return_value = datetime(2024, 7, 22, 6, 0)

            # Verify the switch state
            self.assertEqual(instance_registry["Irrigation_Pump"].on, 0)
            self.assertEqual(instance_registry["Front_Light"].on, 0)
            self.assertEqual(instance_registry["Garden_Light"].on, 0)

            # Measure the execution time of the scheduler
            start_time = time.time()
            await scheduler.run()
            elapsed_time = time.time() - start_time

            # Verify the switch state
            self.assertEqual(instance_registry["Irrigation_Pump"].on, 1)
            self.assertEqual(instance_registry["Front_Light"].on, 1)
            self.assertEqual(instance_registry["Garden_Light"].on, 1)

            # Assert that the elapsed time is within an acceptable range
            self.assertLess(elapsed_time, 3, "Scheduler run took too long")

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        async def test_04_scheduler_run_missed_tasks(self, mock_datetime):
            """Test that tasks are run even if the scheduler starts after the task time."""
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["FakeAutomation"] = Automation(name="FakeAutomation")
            instance_registry["FakeSwitch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time

            mock_datetime.now.return_value = datetime(2024, 7, 19, 3, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 6, 1)
            await scheduler.run()
            self.assertEqual(instance_registry["FakeSwitch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 6, 50)
            await scheduler.run()
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 18, 30)
            await scheduler.run()
            self.assertEqual(instance_registry["FakeSwitch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 18, 50)
            await scheduler.run()
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        async def test_05_scheduler_run_missed_background_tasks(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["DailyAutomation"] = Automation(name="FakeAutomation")
            instance_registry["Daily_Switch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 19, 2, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 3, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 4, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 20, 2, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 20, 3, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 20, 4, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        async def test_06_scheduler_run_background_tasks(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["BackgroundAutomation"] = Automation(name="BackgroundAutomation")
            instance_registry["Cont_Switch"] = LazySwitch(name="FakeSwitch")

            self.assertEqual(instance_registry["Cont_Switch"].on, 0)

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 19, 2, 15)
            await scheduler.run()
            self.assertEqual(instance_registry["Cont_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 12, 18, 43)
            await scheduler.run()
            self.assertEqual(instance_registry["Cont_Switch"].on, 1)

else:
    import asyncio

    class TestMicroScheduler(unittest.TestCase):
        def setUp(self):
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        def tearDown(self):
            self.loop.close()

        def run_async(self, coro):
            """Helper method to run an asynchronous coroutine in the loop."""
            return self.loop.run_until_complete(coro)

        def test_scheduler_init(self):
            scheduler = MicroScheduler(name="Scheduler")
            self.assertIsInstance(scheduler, MicroScheduler)
            self.assertIsInstance(scheduler.schedule, dict)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        def test_scheduler(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["FakeAutomation"] = Automation(name="FakeAutomation")
            instance_registry["FakeSwitch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            self.assertIn("FakeAutomation", scheduler.schedule)
            fake_automation_schedule = scheduler.schedule["FakeAutomation"]["schedule"]
            self.assertIn("monday", fake_automation_schedule)
            self.assertIn("wednesday", fake_automation_schedule)
            self.assertIn("friday", fake_automation_schedule)

            # Test different scheduled times
            times_to_test = [
                (datetime(2024, 7, 19, 6, 0), 1),
                (datetime(2024, 7, 19, 6, 15), 1),
                (datetime(2024, 7, 19, 18, 0), 1),
                (datetime(2024, 7, 19, 18, 30), 1),
                (datetime(2024, 7, 19, 18, 45), 0),
                (datetime(2024, 7, 19, 19, 0), 0),
            ]

            for mock_time, expected_on in times_to_test:
                mock_datetime.now.return_value = mock_time
                self.run_async(scheduler.run())
                self.assertEqual(instance_registry["FakeSwitch"].on, expected_on)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        def test_scheduler_concurrent_execution(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["Irrigation"] = Automation(name="FakeAutomation")
            instance_registry["Garden_Lights"] = Automation(name="FakeAutomation")
            instance_registry["Front_Lights"] = Automation(name="FakeAutomation")
            instance_registry["Irrigation_Pump"] = LazySwitch(name="FakeSwitch")
            instance_registry["Front_Light"] = LazySwitch(name="FakeSwitch")
            instance_registry["Garden_Light"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Set the mock time to a point where all actions should run
            mock_datetime.now.return_value = datetime(2024, 7, 22, 6, 0)

            # Verify the switch state
            self.assertEqual(instance_registry["Irrigation_Pump"].on, 0)
            self.assertEqual(instance_registry["Front_Light"].on, 0)
            self.assertEqual(instance_registry["Garden_Light"].on, 0)

            # Measure the execution time of the scheduler
            start_time = time.time()
            self.run_async(scheduler.run())
            elapsed_time = time.time() - start_time

            # Verify the switch state
            self.assertEqual(instance_registry["Irrigation_Pump"].on, 1)
            self.assertEqual(instance_registry["Front_Light"].on, 1)
            self.assertEqual(instance_registry["Garden_Light"].on, 1)

            # Assert that the elapsed time is within an acceptable range
            self.assertLess(elapsed_time, 3, "Scheduler run took too long")

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        def test_scheduler_run_missed_tasks(self, mock_datetime):
            """Test that tasks are run even if the scheduler starts after the task time."""
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["FakeAutomation"] = Automation(name="FakeAutomation")
            instance_registry["FakeSwitch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time

            mock_datetime.now.return_value = datetime(2024, 7, 19, 3, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 6, 1)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["FakeSwitch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 6, 50)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 18, 30)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["FakeSwitch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 18, 50)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["FakeSwitch"].on, 0)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        def test_scheduler_run_missed_background_tasks(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["DailyAutomation"] = Automation(name="FakeAutomation")
            instance_registry["Daily_Switch"] = LazySwitch(name="FakeSwitch")

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 19, 2, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 3, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 19, 4, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 20, 2, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

            mock_datetime.now.return_value = datetime(2024, 7, 20, 3, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 20, 4, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Daily_Switch"].on, 0)

        @patch('micro_smart_hub.scheduler.datetime', wraps=datetime)
        def test_scheduler_run_background_tasks(self, mock_datetime):
            mock_datetime.strftime = datetime.strftime

            scheduler = MicroScheduler(name="Scheduler")
            instance_registry["BackgroundAutomation"] = Automation(name="FakeAutomation")
            instance_registry["Cont_Switch"] = LazySwitch(name="FakeSwitch")

            self.assertEqual(instance_registry["Cont_Switch"].on, 0)

            # Load the schedule
            schedule_file_path = os.path.join(os.path.dirname(__file__), 'schedule.yaml')
            scheduler.load_schedule(schedule_file_path)

            # Test scheduler starting after the scheduled task time
            mock_datetime.now.return_value = datetime(2024, 7, 19, 2, 15)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Cont_Switch"].on, 1)

            mock_datetime.now.return_value = datetime(2024, 7, 12, 18, 43)
            self.run_async(scheduler.run())
            self.assertEqual(instance_registry["Cont_Switch"].on, 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroScheduler('test_01_scheduler_init'))
    suite.addTest(TestMicroScheduler('test_02_scheduler'))
    suite.addTest(TestMicroScheduler('test_03_scheduler_concurrent_execution'))
    suite.addTest(TestMicroScheduler('test_04_scheduler_run_missed_tasks'))
    suite.addTest(TestMicroScheduler('test_05_scheduler_run_missed_background_tasks'))
    suite.addTest(TestMicroScheduler('test_06_scheduler_run_background_tasks'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

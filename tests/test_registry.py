import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroDevice
from micro_smart_hub.registry import load_modules_from_directory, class_registry, create_instance, load_instances_from_yaml, instance_registry


irrigation_definition = {
    "latitude": 231.0,
    "longitude": 11.22
}

switchbox_definiton = {
    "url": "192.168.0.7"
}


class TestRegistry(unittest.TestCase):

    def test_class_registry(self):
        load_modules_from_directory('micro_smart_hub/automations')
        self.assertTrue("Irrigation" in class_registry)
        load_modules_from_directory('micro_smart_hub/devices')
        self.assertTrue("SwitchBox" in class_registry)

        irrigation = create_instance("Irrigation", **irrigation_definition)
        self.assertTrue(irrigation is not None)
        self.assertIsInstance(irrigation, Automation)

        switchbox = create_instance("SwitchBox", **switchbox_definiton)
        self.assertTrue(switchbox is not None)
        self.assertIsInstance(switchbox, MicroDevice)

    def test_instance_registry(self):
        load_modules_from_directory('micro_smart_hub/automations')
        load_modules_from_directory('micro_smart_hub/devices')

        load_instances_from_yaml('tests/devices.yaml')

        self.assertTrue("Pump" in instance_registry)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestRegistry('test_class_registry'))
    suite.addTest(TestRegistry('test_instance_registry'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

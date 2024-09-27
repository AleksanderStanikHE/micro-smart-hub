import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from micro_smart_hub.automation import Automation
from micro_smart_hub.device import MicroDevice
from micro_registry.registry import load_modules_from_directory, class_registry, create_instance, instance_registry, load_instances_from_yaml, filter_instances_by_base_class


irrigation_definition = {
    "name": "Irrigation",
    "latitude": 231.0,
    "longitude": 11.22
}

switchbox_definiton = {
    "name": "SwitchBox",
    "url": "192.168.0.7"
}


class TestRegistry(unittest.TestCase):

    def test_01_class_registry(self):
        load_modules_from_directory('micro_smart_hub/automations')
        self.assertTrue("Irrigation" in class_registry)
        load_modules_from_directory('micro_smart_hub/devices/blebox')
        self.assertTrue("SwitchBox" in class_registry)

        irrigation = create_instance("Irrigation", **irrigation_definition)
        self.assertTrue(irrigation is not None)
        self.assertIsInstance(irrigation, Automation)

        switchbox = create_instance("SwitchBox", **switchbox_definiton)
        self.assertTrue(switchbox is not None)
        self.assertIsInstance(switchbox, MicroDevice)

    def test_02_instance_registry(self):
        load_modules_from_directory('micro_smart_hub/automations')
        load_modules_from_directory('micro_smart_hub/devices')

        load_instances_from_yaml('tests/config.yaml')

        self.assertTrue("Pump" in instance_registry)
        self.assertTrue("SmartIrrigation" in instance_registry)

        filtered_instances = filter_instances_by_base_class(MicroDevice)

        self.assertTrue("Pump" in filtered_instances)
        self.assertTrue("SmartIrrigation" not in filtered_instances)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestRegistry('test_01_class_registry'))
    suite.addTest(TestRegistry('test_02_instance_registry'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

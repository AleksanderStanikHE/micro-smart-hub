import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
from unittest.mock import Mock, patch

import requests
import time
from micro_smart_hub.device import MicroDevice
from micro_smart_hub.registry import register_class, class_registry, load_instances_from_yaml, instance_registry


@register_class
class FakeThreadedDevice(MicroDevice):

    def load_info(self):
        response = requests.get('fake-threaded-host.com/info')
        self.info = response.json().get('info', {})

    def load_state(self):
        response = requests.get('fake-threaded-host.com/state')
        self.status = response.json().get('state', None)


device_info = {
    "type": "fakeDevice",
    "product": "threadedDevice",
    "hv": "f_d.1.0",
    "fv": "20240305a",
    "id": "8ece4ee6d15c",
    "ip": "192.168.0.197",
}

device_state = {
   "state": 'OK'
}


error_message = (
    "HTTPConnectionPool(host='192.168.0.197', port=80): "
    "Max retries exceeded with url: /state (Caused by NewConnectionError("
    "'<urllib3.connection.HTTPConnection object at 0x1044b5090>: "
    "Failed to establish a new connection: [Errno 61] Connection refused'))"
)


def my_side_effect(url, *args, **kwargs):
    if "info" in url:
        mock = Mock()
        mock.json = lambda: dict(device_info)
        return mock
    else:
        mock = Mock()
        mock.json = lambda: dict(device_state)
        return mock


def exception_side_effect(url, *args, **kwargs):
    raise ConnectionError(error_message)


class TestMicroDevice(unittest.TestCase):

    def setUp(self) -> None:
        fakedevices_file_path = os.path.join(os.path.dirname(__file__), 'fakedevices.yaml')
        load_instances_from_yaml(fakedevices_file_path)

    def test_MicroDevice_register(self):
        self.assertTrue("FakeThreadedDevice" in class_registry)

    def test_MicroDevice_init(self):
        self.assertTrue("Threaded Device" in instance_registry)

        instance = instance_registry["Threaded Device"]
        self.assertEqual(instance.interval, 2.0)

    @patch('requests.get')
    def test_MicroDevice_run(self, mock_get: Mock):
        mock_get.side_effect = my_side_effect
        instance = instance_registry["Threaded Device"]
        self.assertEqual(instance.state.value, "Not Connected")

        instance.start()

        self.assertEqual(instance.state.value, "Connected")
        counter = instance.pooling_counter
        mock_get.side_effect = exception_side_effect

        while instance.pooling_counter <= counter:
            time.sleep(1)
        self.assertEqual(instance.state.value, "Error")

        instance.stop()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestMicroDevice('test_MicroDevice_register'))
    suite.addTest(TestMicroDevice('test_MicroDevice_init'))
    suite.addTest(TestMicroDevice('test_MicroDevice_run'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

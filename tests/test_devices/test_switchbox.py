import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import unittest
import time
from unittest.mock import patch, MagicMock, Mock
from micro_smart_hub.devices.switchbox import SwitchBox
from requests.exceptions import ConnectionError

switchbox_definiton = {
    "url": "192.168.0.197"
}

switch_box_info = {
    "device": {
        "deviceName": "My switchBox LIGHT",
        "type": "switchBox",
        "product": "switchBoxLight",
        "hv": "s_swBL.1.0",
        "fv": "0.1021",
        "universe": 0,
        "apiLevel": "20200831",
        "iconSet": 38,
        "categories": [
            3,
            2
        ],
        "id": "8ece4ee6d15c",
        "ip": "192.168.0.197",
        "availableFv": None
    }
}

switch_box_state = {
    "relays": [
        {
            "relay": 0,
            "state": 0
        }
    ]
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
        mock.json = lambda: dict(switch_box_info)
        return mock
    else:
        mock = Mock()
        mock.json = lambda: dict(switch_box_state)
        return mock


def exception_with_sleep(url, *args, **kwargs):
    time.sleep(2)
    raise ConnectionError(error_message)


class TestSwitchBox(unittest.TestCase):

    @patch('requests.post')
    @patch('requests.get')
    def test_switchbox_init(self, mock_get: Mock, mock_post: Mock):

        mock_get.side_effect = my_side_effect
        switch_box = SwitchBox(switchbox_definiton)
        switch_box.start()

        self.assertIsInstance(switch_box.info["deviceName"], str)
        self.assertIsInstance(switch_box.info["type"], str)
        self.assertIsInstance(switch_box.info["hv"], str)
        self.assertIsInstance(switch_box.info["fv"], str)
        self.assertIsInstance(switch_box.info["universe"], int)
        self.assertIsInstance(switch_box.info["apiLevel"], str)

        self.assertIsInstance(switch_box.relays[0], dict)
        self.assertEqual(switch_box.on, 0)

    @patch('requests.post')
    @patch('requests.get')
    def test_switchbox_call(self, mock_get: Mock, mock_post: Mock):
        mock_get.side_effect = my_side_effect
        switch_box = SwitchBox(switchbox_definiton)
        switch_box.start()

        # Simulate successful communication initially
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'relays': [{'state': 0}]})
        mock_post.return_value = MagicMock(status_code=200)

        switch_box.on = 0
        self.assertEqual(switch_box.on, 0)

        # Simulate successful communication initially
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'relays': [{'state': 1}]})
        mock_post.return_value = MagicMock(status_code=200)

        switch_box.on = 1
        self.assertEqual(switch_box.on, 1)

        # Simulate successful communication initially
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'relays': [{'state': 0}]})
        mock_post.return_value = MagicMock(status_code=200)

        switch_box.on = 0
        self.assertEqual(switch_box.on, 0)

        # Simulate successful communication initially
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'relays': [{'state': 1}]})
        mock_post.return_value = MagicMock(status_code=200)

        switch_box.on = 1
        self.assertEqual(switch_box.on, 1)

    @patch('requests.post')
    @patch('requests.get')
    def test_switchbox_no_device(self, mock_get, mock_post):
        mock_get.side_effect = my_side_effect
        switch_box = SwitchBox(switchbox_definiton)
        switch_box.start()

        mock_get.side_effect = exception_with_sleep
        mock_post.side_effect = exception_with_sleep

        with self.assertRaises(ConnectionError):
            switch_box.on = 1

    @patch('requests.post')
    @patch('requests.get')
    def test_switch_broken_communication(self, mock_get, mock_post):
        switch_box_state["relays"][0]['state'] = 14
        mock_get.side_effect = my_side_effect
        switch_box = SwitchBox(switchbox_definiton)
        switch_box.start()

        error_message = (
            "HTTPConnectionPool(host='192.168.0.197', port=80): "
            "Max retries exceeded with url: /state (Caused by NewConnectionError("
            "'<urllib3.connection.HTTPConnection object at 0x1044b5090>: "
            "Failed to establish a new connection: [Errno 61] Connection refused'))"
        )

        # Simulate successful communication initially
        # mock_get.return_value.json = lambda: {'relays': [{'state': 14}]}
        mock_post.return_value = MagicMock(status_code=200)

        self.assertEqual(switch_box.on, 14)

        # Simulate successful communication initially
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'relays': [{'state': 0}]})
        mock_post.return_value = MagicMock(status_code=200)

        switch_box.on = 1
        self.assertEqual(switch_box.on, 1)

        exception = ConnectionError(error_message)
        mock_get.side_effect = exception
        mock_post.side_effect = exception

        self.assertEqual(switch_box.on, 1)

        with self.assertRaises(ConnectionError):
            switch_box.on = 0

        switch_box_state["relays"][0]['state'] = 1

        counter = switch_box.pooling_counter
        mock_get.side_effect = my_side_effect

        while switch_box.pooling_counter <= counter:
            time.sleep(1)

        self.assertEqual(switch_box.on, 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestSwitchBox('test_switchbox_init'))
    suite.addTest(TestSwitchBox('test_switchbox_call'))
    suite.addTest(TestSwitchBox('test_switchbox_no_device'))
    suite.addTest(TestSwitchBox('test_switch_broken_communication'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

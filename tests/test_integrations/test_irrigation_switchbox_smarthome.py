import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import unittest
from datetime import datetime
from unittest.mock import patch, Mock
from micro_smart_hub.automations.irrigation import Irrigation
from micro_smart_hub.scheduler import MicroScheduler
from micro_smart_hub.devices.blebox.switchbox import SwitchBox
from micro_registry.registry import instance_registry

irrigation_scenarios = {
    "Wind_OK_Precipitation_WRONG": {"url": "https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=49.991&longitude=18.3508&hourly=temperature_2m,wind_speed_10m,soil_moisture_1_to_3cm",
                                    "date": "2024-07-17",
                                    "moisture_threshold": 0.12,
                                    "wind_threshold": 4.0,
                                    "hour": 5,
                                    "result": 0},
    "Wind_WRONG_Precipitation_WRONG": {"url": "https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=49.991&longitude=18.3508&hourly=temperature_2m,wind_speed_10m,soil_moisture_1_to_3cm",
                                       "date": "2024-07-01",
                                       "moisture_threshold": 0.14,
                                       "wind_threshold": 4.0,
                                       "hour": 4,
                                       "result": 0},
    "Wind_WRONG_Precipitation_OK": {"url": "https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=49.991&longitude=18.3508&hourly=temperature_2m,wind_speed_10m,soil_moisture_1_to_3cm",
                                    "date": "2024-07-05",
                                    "moisture_threshold": 0.14,
                                    "wind_threshold": 4.0,
                                    "hour": 4,
                                    "result": 0},
    "Wind_OK_Precipitation_OK": {"url": "https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=49.991&longitude=18.3508&hourly=temperature_2m,wind_speed_10m,soil_moisture_1_to_3cm",
                                 "date": "2024-06-26",
                                 "moisture_threshold": 0.5,
                                 "wind_threshold": 10.0,
                                 "hour": 4,
                                 "result": 1}
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

irrigation_definition = {
    "latitude": 49.995501454573485,
    "longitude": 18.34122645754075
}

switchbox_definiton = {
    "url": "192.168.0.197"
}


def my_side_effect(url, *args, **kwargs):
    if "info" in url:
        mock = Mock()
        mock.json = lambda: dict(switch_box_info)
        return mock
    else:
        mock = Mock()
        mock.json = lambda: dict(switch_box_state)
        return mock


class TestIrrigationSwitchBoxSmartHome(unittest.TestCase):

    @patch('micro_smart_hub.devices.blebox.switchbox.requests')
    @patch('micro_smart_hub.automations.irrigation.datetime')
    def test_system_run(self, mock_datetime, mock_get):

        mock_get.get = Mock()
        mock_get.get.side_effect = my_side_effect
        smart_home = MicroScheduler()

        instance_registry["Irrigation"] = Irrigation(**irrigation_definition)
        instance_registry["Pump"] = SwitchBox(**switchbox_definiton)
        schedule_file_path = os.path.join(os.path.dirname(__file__), 'irrigation_switchbox.yaml')
        smart_home.load_schedule(schedule_file_path)

        irrigation = instance_registry["Irrigation"]

        for key, params in irrigation_scenarios.items():
            irrigation.url = params['url']
            irrigation.soil_moisture_threshold = params["moisture_threshold"]
            irrigation.wind_threshold = params["wind_threshold"]
            mock_datetime.now.return_value = datetime.strptime(params["date"], "%Y-%m-%d")
            hour = params["hour"]
            result = params["result"]
            switch = instance_registry["Pump"]
            irrigation.run(True, {"current_hour": hour}, [switch])
            self.assertTrue(switch.on == result, f"Wrong scenario {key}.")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIrrigationSwitchBoxSmartHome('test_system_run'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

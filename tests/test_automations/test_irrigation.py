import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import unittest
from datetime import datetime
from unittest.mock import patch, Mock
from micro_smart_hub.device import MicroSwitch
from micro_smart_hub.automations.irrigation import Irrigation

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

irrigation_definition = {
    "latitude": 49.995501454573485,
    "longitude": 18.34122645754075
}


class TestIrrigation(unittest.TestCase):

    @patch('micro_smart_hub.automations.irrigation.datetime')
    def test_irrigation_run(self, mock_datetime: Mock):
        irrigation = Irrigation(**irrigation_definition)
        for key, params in irrigation_scenarios.items():
            irrigation.url = params['url']
            irrigation.soil_moisture_threshold = params["moisture_threshold"]
            irrigation.wind_threshold = params["wind_threshold"]
            mock_datetime.now.return_value = datetime.strptime(params["date"], "%Y-%m-%d")
            hour = params["hour"]
            result = params["result"]
            switch = MicroSwitch()
            irrigation.run(True, {"current_hour": hour}, [switch])
            self.assertTrue(switch.on == result, f"Wrong scenario {key}.")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIrrigation('test_irrigation_run'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import unittest
from datetime import datetime
from unittest.mock import patch, Mock
from micro_smart_hub.device import IoTSwitch
from micro_smart_hub.automations.irrigation import Irrigation

irrigation_scenarios = {
    "Wind_OK_Precipitation_WRONG": {"url": "https://api.open-meteo.com/v1/forecast?latitude=49.995501454573485&longitude=18.34122645754075&current=temperature_2m&hourly=wind_speed_10m,soil_moisture_1_to_3cm&start_date=2024-07-17&end_date=2024-07-19",
                                    "date": "2024-07-17",
                                    "hour": 5,
                                    "result": 0},
    "Wind_WRONG_Precipitation_WRONG": {"url": "https://api.open-meteo.com/v1/forecast?latitude=49.995501454573485&longitude=18.34122645754075&current=temperature_2m&hourly=wind_speed_10m,soil_moisture_1_to_3cm&start_date=2024-07-01&end_date=2024-07-03",
                                       "date": "2024-07-01",
                                       "hour": 4,
                                       "result": 0},
    "Wind_WRONG_Precipitation_OK": {"url": "https://api.open-meteo.com/v1/forecast?latitude=49.995501454573485&longitude=18.34122645754075&current=temperature_2m&hourly=wind_speed_10m,soil_moisture_1_to_3cm&start_date=2024-07-05&end_date=2024-07-07",
                                    "date": "2024-07-05",
                                    "hour": 4,
                                    "result": 0},
    "Wind_OK_Precipitation_OK": {"url": "https://api.open-meteo.com/v1/forecast?latitude=49.995501454573485&longitude=18.34122645754075&current=temperature_2m&hourly=wind_speed_10m,soil_moisture_1_to_3cm&start_date=2024-06-26&end_date=2024-06-28",
                                 "date": "2024-06-26",
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
        irrigation = Irrigation(irrigation_definition)
        for key, params in irrigation_scenarios.items():
            mock_datetime.now.return_value = datetime.strptime(params["date"], "%Y-%m-%d")
            hour = params["hour"]
            result = params["result"]
            switch = IoTSwitch()
            irrigation.run(True, {"current_hour": hour}, [switch])
            self.assertTrue(switch.on == result, f"Wrong scenario {key}.")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestIrrigation('test_irrigation_run'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

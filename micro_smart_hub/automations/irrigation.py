import numpy as np
import requests
from datetime import datetime, timedelta
from micro_smart_hub.automation import Automation
from micro_smart_hub.registry import register_class


@register_class
class Irrigation(Automation):
    def __init__(self, definition={}) -> None:
        super().__init__(definition)
        self.latitude = self.definition.get("latitude", 0.0)
        self.longitude = self.definition.get("longitude", 0.0)
        self.soil_moisture_threshold = 0.2
        self.wind_threshold = 4.0
        self.wind_data = np.zeros(72)
        self.soil_moisture_data = np.zeros(72)
        self.url = f"https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&current=temperature_2m&hourly=precipitation_probability,precipitation,wind_speed_10m,soil_temperature_0cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm"

    def check_soil_moisture(self, moisture_data, start_hour, end_hour, threshold) -> True:
        """
        Check if the average soil moisture between start_hour and end_hour is higher than the given threshold.

        Parameters:
        moisture_data (np.array): Array of soil moisture data.
        start_hour (int): The start hour of the interval.
        end_hour (int): The end hour of the interval.
        threshold (float): The threshold value for the average soil moisture.

        Returns:
        bool: True if the average soil moisture in the interval is higher than the threshold, False otherwise.
        """
        if end_hour > len(moisture_data):
            raise ValueError("End hour exceeds the length of the data array.")

        # Slice the data for the specified interval
        interval_data = moisture_data[start_hour:end_hour]

        # Calculate the average soil moisture for the interval
        average_moisture = np.mean(interval_data)

        # Check if the average is higher than the threshold
        return average_moisture < threshold

    def wind_silence(self, wind_data, at_hour, threshold) -> True:
        if at_hour > len(wind_data):
            raise ValueError("End hour exceeds the length of the data array.")
        return wind_data[at_hour] < threshold

    def should_irrigate(self, current_hour) -> bool:
        if self.wind_silence(self.wind_data, current_hour, self.wind_threshold):
            if self.check_soil_moisture(self.soil_moisture_data, 24, 48, self.soil_moisture_threshold):
                return True
        return False

    def run(self, action, parameters, devices) -> None:
        current_hour = parameters["current_hour"]
        current_date = datetime.now()
        start_date = current_date.strftime("%Y-%m-%d")
        future_date = current_date + timedelta(days=2)
        end_date = future_date.strftime("%Y-%m-%d")
        response = requests.get(self.url + f"&start_date={start_date}&end_date={end_date}")
        weather_data = response.json()
        self.wind_data = np.array(weather_data['hourly']['wind_speed_10m'])
        self.soil_moisture_data = np.array(weather_data['hourly']['soil_moisture_1_to_3cm'])
        if self.should_irrigate(current_hour):
            action = True
        else:
            action = False
        super().run(action, parameters, devices)

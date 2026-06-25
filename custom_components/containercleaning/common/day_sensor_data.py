from datetime import datetime, timedelta
from ..const.const import _LOGGER
from typing import List, TypedDict

class WasteItem(TypedDict):
    type: str
    date: datetime

class DaySensorData:
    def __init__(self, waste_data_formatted: List[WasteItem], default_label: str):
        today = datetime.now().strftime("%d-%m-%Y")

        self.waste_data_formatted = sorted(
            waste_data_formatted, key=lambda d: d["date"]
            )
        self.today_date = datetime.strptime(today, "%d-%m-%Y")
        self.tomorrow_date = self.today_date + timedelta(days=1)
        self.day_after_tomorrow_date = self.today_date + timedelta(days=2)
        self.default_label = default_label

        self.waste_data_today = self.__gen_day_sensor(self.today_date)
        self.waste_data_tomorrow = self.__gen_day_sensor(self.tomorrow_date)
        self.waste_data_dot = self.__gen_day_sensor(self.day_after_tomorrow_date)

        self.data = self._gen_day_sensor_data()

    def __gen_day_sensor(self, date):
        day = []
        try:
            day.extend(
                waste["type"]
                for waste in self.waste_data_formatted
                if waste["date"] == date
            )
            if not day:
                day.append(self.default_label)
        except Exception as err:
            _LOGGER.warning("Could not generate day sensor for date %s: %s", date, err)
        return day

    def _gen_day_sensor_data(self):
        day_sensor = {}
        try:
            day_sensor["today"] = ", ".join(self.waste_data_today)
            day_sensor["tomorrow"] = ", ".join(self.waste_data_tomorrow)
            day_sensor["day_after_tomorrow"] = ", ".join(self.waste_data_dot)
            _LOGGER.debug("Day sensors — today: %s, tomorrow: %s, day after: %s",
                day_sensor["today"], day_sensor["tomorrow"], day_sensor["day_after_tomorrow"])
        except Exception as err:
            _LOGGER.warning("Could not generate day sensor data: %s", err)
        return day_sensor

    @property
    def day_sensor_data(self):
        return self.data
from datetime import date, datetime
from ..const.const import _LOGGER
from typing import List, TypedDict, Optional


class WasteItem(TypedDict):
    type: str
    date: datetime


class NextSensorData:

    def __init__(self, waste_data_after_date_selected: List[WasteItem]):

        self.waste_data_after_date_selected = sorted(
            waste_data_after_date_selected, key=lambda d: d["date"]
        )
        self.today_date: datetime = datetime.now()

        self.next_waste_date: Optional[datetime] = self.__get_next_waste_date()
        self.next_waste_in_days = self.__get_next_waste_in_days()
        self.next_waste_type = self.__get_next_waste_type()

        self.data = self._gen_next_sensor_data()

    def __get_next_waste_date(self) -> Optional[datetime]:
        try:
            return self.waste_data_after_date_selected[0]["date"]
        except IndexError:
            _LOGGER.debug("No upcoming cleaning scheduled after the selected date")
            return None

    def __get_next_waste_in_days(self):
        try:
            if self.next_waste_date is None:
                return None
            return abs(self.next_waste_date.date() - date.today()).days
        except Exception as err:
            _LOGGER.warning("Could not calculate days until next cleaning: %s", err)
            return None

    def __get_next_waste_type(self):
        try:
            if self.next_waste_date is None:
                return None
            types = [
                waste["type"]
                for waste in self.waste_data_after_date_selected
                if waste["date"] == self.next_waste_date
            ]
            return ", ".join(types) if types else None
        except Exception as err:
            _LOGGER.warning("Could not determine next container type: %s", err)
            return None

    def _gen_next_sensor_data(self):
        try:
            data = {
                "next_date": self.next_waste_date,
                "next_in_days": self.next_waste_in_days,
                "next_type": self.next_waste_type,
            }
            _LOGGER.debug("Next cleaning: type=%s, date=%s, in %s day(s)",
                data["next_type"], data["next_date"], data["next_in_days"])
            return data
        except Exception as err:
            _LOGGER.warning("Could not generate next sensor data: %s", err)
            return {}

    @property
    def next_sensor_data(self):
        return self.data
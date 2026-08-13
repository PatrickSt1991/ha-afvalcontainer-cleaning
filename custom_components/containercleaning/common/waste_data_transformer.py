from datetime import datetime, timedelta
from typing import List

from ..common.day_sensor_data import DaySensorData, WasteItem
from ..common.next_sensor_data import NextSensorData
from ..const.const import _LOGGER

# import sys
# def excepthook(type, value, traceback):
#     _LOGGER.error(value)
# sys.excepthook = excepthook


class WasteDataTransformer(object):

    ##########################################################################
    #  INIT
    ##########################################################################
    def __init__(
        self,
        waste_data_raw,
        exclude_pickup_today,
        exclude_list,
    ):
        if not isinstance(waste_data_raw, list):
            raise ValueError(
                f"waste_data_raw must be a list, got {type(waste_data_raw).__name__}"
            )
        self.waste_data_raw = self.__normalize_waste_data_raw(waste_data_raw)
        self.waste_data_raw.sort(key=lambda item: item["date"])
        self.exclude_pickup_today = exclude_pickup_today
        self.exclude_types = {
            item.strip().lower()
            for item in str(exclude_list).split(",")
            if item.strip()
        }

        TODAY = datetime.now().strftime("%d-%m-%Y")
        self.DATE_TODAY = datetime.strptime(TODAY, "%d-%m-%Y")
        self.DATE_TOMORROW = datetime.strptime(TODAY, "%d-%m-%Y") + timedelta(days=1)

        (
            self._waste_data_with_today,
            self._waste_data_without_today,
        ) = self.__structure_waste_data()  # type: ignore

        (
            self._waste_data_provider,
            self._waste_types_provider,
            self._waste_data_custom,
            self._waste_types_custom,
        ) = self.__gen_sensor_waste_data()

    ##########################################################################
    # STRUCTURE ALL WASTE DATA IN CUSTOM FORMAT
    #########################################################################

    def __normalize_waste_data_raw(self, waste_data_raw) -> List[WasteItem]:
        """Normalize and validate raw entries once so later stages can reuse parsed values."""
        normalized: List[WasteItem] = []
        for item in waste_data_raw:
            item_type = str(item.get("type", "")).strip().lower()
            if not item_type:
                continue

            raw_date = item.get("date")
            if isinstance(raw_date, datetime):
                item_date = raw_date
            elif isinstance(raw_date, str):
                item_date = datetime.strptime(raw_date, "%Y-%m-%d")
            else:
                raise ValueError(f"Invalid date type for waste item: {type(raw_date).__name__}")

            normalized.append({"type": item_type, "date": item_date})

        return normalized

    def __structure_waste_data(self):
        try:
            waste_data_with_today = {}
            waste_data_without_today = {}
            known_waste_types = set()

            for item in self.waste_data_raw:
                item_date = item["date"]
                item_name = item["type"]
                if item_name in self.exclude_types:
                    continue

                known_waste_types.add(item_name)

                if item_name not in waste_data_with_today and item_date >= self.DATE_TODAY:
                    waste_data_with_today[item_name] = item_date

                if item_name not in waste_data_without_today and item_date > self.DATE_TODAY:
                    waste_data_without_today[item_name] = item_date

            for item_name in known_waste_types:
                waste_data_with_today.setdefault(item_name, None)
                waste_data_without_today.setdefault(item_name, None)

            _LOGGER.debug("Structured %d unique waste types", len(waste_data_with_today))
            return waste_data_with_today, waste_data_without_today
        except Exception as err:
            _LOGGER.error("Failed to structure waste data: %s", err)

    ##########################################################################
    # GENERATE REQUIRED DATA FOR HASS SENSORS
    ##########################################################################
    def __gen_sensor_waste_data(self):
        if self.exclude_pickup_today.casefold() in ("false", "no"):
            date_selected = self.DATE_TODAY
            waste_data_provider = self._waste_data_with_today
        else:
            date_selected = self.DATE_TOMORROW
            waste_data_provider = self._waste_data_without_today

        waste_types_provider = []
        try:
            waste_types_provider = sorted(
                {
                    waste["type"]
                    for waste in self.waste_data_raw
                    if waste["type"] not in self.exclude_types
                }
            )

        except Exception as err:
            _LOGGER.warning("Failed to collect waste types from raw data: %s", err)

        waste_data_formatted: List[WasteItem] = []
        try:
            waste_data_formatted = [
                {
                    "type": waste["type"],
                    "date": waste["date"],
                }
                for waste in self.waste_data_raw
                if waste["type"] in waste_types_provider
            ]

        except Exception as err:
            _LOGGER.warning("Failed to format waste data: %s", err)

        days = DaySensorData(waste_data_formatted)

        waste_data_after_date_selected: List[WasteItem] = []
        try:
            waste_data_after_date_selected = [
                waste for waste in waste_data_formatted if waste["date"] >= date_selected
            ]
        except Exception as err:
            _LOGGER.warning("Failed to filter waste data by date: %s", err)

        next_data = NextSensorData(waste_data_after_date_selected)

        waste_data_custom = {}
        try:
            waste_data_custom = {**next_data.next_sensor_data, **days.day_sensor_data}
        except Exception as err:
            _LOGGER.warning("Failed to merge custom sensor data: %s", err)

        waste_types_custom = []
        try:
            waste_types_custom = list(sorted(waste_data_custom.keys()))
        except Exception as err:
            _LOGGER.warning("Failed to sort custom waste types: %s", err)

        _LOGGER.debug("Generated %d custom sensors (%s)", len(waste_types_custom), ", ".join(waste_types_custom))

        return (
            waste_data_provider,
            waste_types_provider,
            waste_data_custom,
            waste_types_custom,
        )

    ##########################################################################
    #  PROPERTIES FOR EXECUTION
    ##########################################################################

    @property
    def waste_data_with_today(self):
        return self._waste_data_with_today

    @property
    def waste_data_without_today(self):
        return self._waste_data_without_today

    @property
    def waste_data_provider(self):
        return self._waste_data_provider

    @property
    def waste_types_provider(self):
        return self._waste_types_provider

    @property
    def waste_data_custom(self):
        return self._waste_data_custom

    @property
    def waste_types_custom(self):
        return self._waste_types_custom

    @property
    def waste_data_events(self):
        """Return every known pickup (past and future) after exclude_list filtering."""
        return [
            item
            for item in self.waste_data_raw
            if item["type"] not in self.exclude_types
        ]

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.const import UnitOfTime
from datetime import datetime, date
import hashlib

from .const.const import (
    ATTR_DAYS_UNTIL_COLLECTION_DATE,
    CONF_ID,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_DATE_ISOFORMAT,
    DOMAIN,
    SENSOR_ICON,
)


def _format_sensor_name(raw_value: str) -> str:
    """Return a human-friendly fallback name for sensors."""
    acronyms = {"gft", "pmd"}
    parts = raw_value.replace("-", " ").replace("_", " ").split()
    formatted = [part.upper() if part.casefold() in acronyms else part.capitalize() for part in parts]
    return " ".join(formatted)


class CustomSensor(CoordinatorEntity, SensorEntity):
    """Representation of a custom-based waste sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, waste_type, config):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.waste_type = waste_type
        self.config = config
        self._collector = str(config.get(CONF_COLLECTOR, "")).strip().lower()
        self._postal_code = str(config.get(CONF_POSTAL_CODE, "")).strip().upper()
        self._street_number = str(config.get(CONF_STREET_NUMBER, "")).strip()
        self._suffix = str(config.get(CONF_SUFFIX, "")).strip().lower()
        self._device_key = f"{self._collector}:{self._postal_code}:{self._street_number}:{self._suffix}"
        self._date_isoformat = str(config.get(CONF_DATE_ISOFORMAT)).lower()
        self._icon = SENSOR_ICON
        key = self.waste_type.replace("-", "_").replace(" ", "_")
        self._attr_translation_key = f"custom_{key}"
        self._attr_name = _format_sensor_name(key)
        self._unique_id = hashlib.sha1(
            (
                f"{waste_type}{config.get(CONF_ID)}{config.get(CONF_COLLECTOR)}"
                f"{config.get(CONF_POSTAL_CODE)}{config.get(CONF_STREET_NUMBER)}"
                f"{config.get(CONF_SUFFIX, '')}"
            ).encode("utf-8")
        ).hexdigest()

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata so translated entity naming resolves correctly."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name="Container Cleaning",
            manufacturer="Container Cleaning",
            model=self._collector or "cleanprofs",
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if "next_in_days" in self.waste_type.lower():
            return SensorDeviceClass.DURATION
        if isinstance(self._get_value(), datetime):
            return SensorDeviceClass.TIMESTAMP
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit for day-count sensors."""
        if "next_in_days" in self.waste_type.lower():
            return UnitOfTime.DAYS
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        value = self._get_value()
        if value is None:
            return None
        if "next_in_days" in self.waste_type.lower() and isinstance(value, (int, float)):
            return value
        if isinstance(value, datetime):
            if self._date_isoformat in ("true", "yes"):
                return value.isoformat()
            return value.date()
        return str(value)

    @property
    def extra_state_attributes(self):
        """Return the attributes of the sensor."""
        attrs = {}

        if "next_date" in self.waste_type.lower():
            value = self._get_value()
            if isinstance(value, datetime):
                attrs[ATTR_DAYS_UNTIL_COLLECTION_DATE] = (value.date() - date.today()).days
            else:
                attrs[ATTR_DAYS_UNTIL_COLLECTION_DATE] = None

        return attrs

    def _get_value(self):
        """Return the raw value for this waste type from coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data["waste_data_custom"].get(self.waste_type)

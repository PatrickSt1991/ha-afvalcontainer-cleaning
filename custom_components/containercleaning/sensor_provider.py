#!/usr/bin/env python3
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime, date, timedelta
import hashlib

from .const.const import (
    ATTR_DAYS_UNTIL_COLLECTION_DATE,
    ATTR_IS_COLLECTION_DATE_DAY_AFTER_TOMORROW,
    ATTR_IS_COLLECTION_DATE_TODAY,
    ATTR_IS_COLLECTION_DATE_TOMORROW,
    CONF_EXCLUDE_PICKUP_TODAY,
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


class ProviderSensor(CoordinatorEntity, SensorEntity):
    """Representation of a provider-based waste sensor."""

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
        self._exclude_pickup_today = str(config.get(CONF_EXCLUDE_PICKUP_TODAY)).lower()
        self._date_isoformat = str(config.get(CONF_DATE_ISOFORMAT)).lower()
        self._icon = SENSOR_ICON
        key = self.waste_type.replace("-", "_").replace(" ", "_")
        self._attr_translation_key = f"provider_{key}"
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
        if isinstance(self._get_collection_date(), datetime):
            return SensorDeviceClass.TIMESTAMP
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        collection_date = self._get_collection_date()
        if collection_date is None:
            return None
        if isinstance(collection_date, datetime):
            if self._date_isoformat in ("true", "yes"):
                return collection_date.isoformat()
            return collection_date.date()
        return str(collection_date)

    @property
    def extra_state_attributes(self):
        """Return the attributes of the sensor."""
        collection_date = self._get_collection_date()
        attrs = {}

        if isinstance(collection_date, datetime):
            today = date.today()
            delta = collection_date.date() - today
            attrs[ATTR_DAYS_UNTIL_COLLECTION_DATE] = delta.days
            attrs[ATTR_IS_COLLECTION_DATE_TODAY] = collection_date.date() == today
            attrs[ATTR_IS_COLLECTION_DATE_TOMORROW] = collection_date.date() == today + timedelta(days=1)
            attrs[ATTR_IS_COLLECTION_DATE_DAY_AFTER_TOMORROW] = collection_date.date() == today + timedelta(days=2)
        else:
            attrs[ATTR_DAYS_UNTIL_COLLECTION_DATE] = None
            attrs[ATTR_IS_COLLECTION_DATE_TODAY] = None
            attrs[ATTR_IS_COLLECTION_DATE_TOMORROW] = None
            attrs[ATTR_IS_COLLECTION_DATE_DAY_AFTER_TOMORROW] = None

        return attrs

    def _get_collection_date(self):
        """Return the collection date for this waste type from coordinator data."""
        if self.coordinator.data is None:
            return None
        waste_data = (
            self.coordinator.data["waste_data_with_today"]
            if self._exclude_pickup_today in ("false", "no")
            else self.coordinator.data["waste_data_without_today"]
        )
        return waste_data.get(self.waste_type)

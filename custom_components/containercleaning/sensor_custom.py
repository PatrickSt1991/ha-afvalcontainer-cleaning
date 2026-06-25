from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from datetime import datetime, date
import hashlib

from .const.const import (
    _LOGGER,
    ATTR_LAST_UPDATE,
    ATTR_DAYS_UNTIL_COLLECTION_DATE,
    CONF_DEFAULT_LABEL,
    CONF_ID,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_DATE_ISOFORMAT,
    SENSOR_ICON,
    SENSOR_PREFIX,
)


class CustomSensor(CoordinatorEntity, SensorEntity):
    """Representation of a custom-based waste sensor."""

    def __init__(self, coordinator, waste_type, config):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.waste_type = waste_type
        self.config = config
        self._id_name = config.get(CONF_ID)
        self._default_label = config.get(CONF_DEFAULT_LABEL)
        self._date_isoformat = str(config.get(CONF_DATE_ISOFORMAT)).lower()
        self._name = (
            SENSOR_PREFIX + (f"{self._id_name} " if self._id_name else "")
        ) + waste_type
        self._icon = SENSOR_ICON
        self._unique_id = hashlib.sha1(
            (
                f"{waste_type}{config.get(CONF_ID)}{config.get(CONF_COLLECTOR)}"
                f"{config.get(CONF_POSTAL_CODE)}{config.get(CONF_STREET_NUMBER)}"
                f"{config.get(CONF_SUFFIX, '')}"
            ).encode("utf-8")
        ).hexdigest()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def translation_key(self) -> str:
        """Return the translation key for the sensor, based on waste type."""
        key = self.waste_type.replace("-", "_").replace(" ", "_")
        return f"custom_{key}"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if isinstance(self._get_value(), datetime):
            return SensorDeviceClass.TIMESTAMP
        return None

    @property
    def state(self):
        """Return the state of the sensor."""
        value = self._get_value()
        if value is None:
            return self._default_label
        if isinstance(value, datetime):
            if self._date_isoformat in ("true", "yes"):
                return value.isoformat()
            return value.date()
        return str(value)

    @property
    def extra_state_attributes(self):
        """Return the attributes of the sensor."""
        last_update = (
            self.coordinator.last_updated.isoformat()
            if self.coordinator.last_updated
            else None
        )
        attrs = {ATTR_LAST_UPDATE: last_update}

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

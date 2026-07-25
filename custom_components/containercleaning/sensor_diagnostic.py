from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import hashlib

from .const.const import (
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    DOMAIN,
)


def _provider_display_name(provider: str) -> str:
    """Return a human-friendly provider display name."""
    mapping = {
        "cleanprofs": "CleanProfs",
    }
    provider_key = provider.strip().lower()
    if provider_key in mapping:
        return mapping[provider_key]
    return provider.strip().title() if provider.strip() else "Container Cleaning"


class LastServerUpdateSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor showing the last successful server fetch timestamp."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "diagnostic_last_server_update"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:cloud-clock"

    def __init__(self, coordinator, config):
        """Initialize the diagnostic sensor."""
        super().__init__(coordinator)
        self.config = config
        self._collector = str(config.get(CONF_COLLECTOR, "")).strip().lower()
        self._postal_code = str(config.get(CONF_POSTAL_CODE, "")).strip().upper()
        self._street_number = str(config.get(CONF_STREET_NUMBER, "")).strip()
        self._suffix = str(config.get(CONF_SUFFIX, "")).strip().lower()
        self._device_key = f"{self._collector}:{self._postal_code}:{self._street_number}:{self._suffix}"
        self._attr_unique_id = hashlib.sha1(
            (
                f"last_server_update:{self._collector}:{self._postal_code}:"
                f"{self._street_number}:{self._suffix}"
            ).encode("utf-8")
        ).hexdigest()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata grouped with other integration sensors."""
        provider_name = _provider_display_name(self._collector)
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name=provider_name,
            manufacturer="Container Cleaning",
            model=provider_name,
        )

    @property
    def native_value(self):
        """Return the last successful coordinator update time."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("last_server_update")

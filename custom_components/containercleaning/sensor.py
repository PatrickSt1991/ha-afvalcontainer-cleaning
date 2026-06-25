import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA

from .const.const import (
    _LOGGER,
    CONF_COLLECTOR,
    CONF_DEFAULT_LABEL,
    CONF_EXCLUDE_LIST,
    CONF_EXCLUDE_PICKUP_TODAY,
    CONF_DATE_ISOFORMAT,
    CONF_ID,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    DOMAIN,
)
from .sensor_custom import CustomSensor
from .sensor_provider import ProviderSensor


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_COLLECTOR, default="cleanprofs"): cv.string,
        vol.Required(CONF_POSTAL_CODE): cv.string,
        vol.Required(CONF_STREET_NUMBER): cv.string,
        vol.Optional(CONF_SUFFIX, default=""): cv.string,
        vol.Optional(CONF_EXCLUDE_PICKUP_TODAY, default=True): cv.boolean,
        vol.Optional(CONF_DATE_ISOFORMAT, default=False): cv.boolean,
        vol.Optional(CONF_EXCLUDE_LIST, default=""): cv.string,
        vol.Optional(CONF_DEFAULT_LABEL, default="geen"): cv.string,
        vol.Optional(CONF_ID, default=""): cv.string,
    }
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry using the shared coordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data is None:
        _LOGGER.error("No data available from coordinator; sensors cannot be created.")
        return

    waste_types_provider = set(coordinator.data["waste_data_with_today"].keys())
    waste_types_custom = set(coordinator.data["waste_data_custom"].keys())

    entities = [
        ProviderSensor(coordinator, waste_type, entry.data)
        for waste_type in waste_types_provider
    ] + [
        CustomSensor(coordinator, waste_type, entry.data)
        for waste_type in waste_types_custom
    ]

    if not entities:
        _LOGGER.error("No entities created; check configuration or collector output.")
        return

    _LOGGER.debug("Adding %d sensors for Container Cleaning", len(entities))
    async_add_entities(entities)


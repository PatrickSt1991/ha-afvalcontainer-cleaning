from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .collector.collector import MainCollector
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
    SCAN_INTERVAL,
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up sensors using the platform schema."""
    if not discovery_info:
        _LOGGER.error("No discovery information provided; sensors cannot be created.")
        return

    await _setup_sensors(hass, discovery_info, async_add_entities)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry."""
    await _setup_sensors(hass, entry.data, async_add_entities)


async def _setup_sensors(hass, config, async_add_entities):
    """Common setup logic for platform and config entry."""
    _LOGGER.debug(
        f"Setting up Container Cleaning sensors for provider: {config.get(CONF_COLLECTOR)}."
    )

    # Initialize data handlers
    data = ContainerCleaningData(hass, config)

    # Perform an initial update at startup
    await hass.async_add_executor_job(data.update)

    # Schedule periodic updates every 4 hours
    update_interval = timedelta(hours=4)

    def schedule_update(_):
        """Safely schedule the update."""
        hass.loop.call_soon_threadsafe(hass.async_add_executor_job, data.update)

    async_track_time_interval(hass, schedule_update, update_interval)

    try:
        waste_types_provider = set(data.waste_data_with_today.keys())
        waste_types_custom = set(data.waste_data_custom.keys())
    except Exception as err:
        _LOGGER.error(f"Failed to fetch container types: {err}")
        return

    # Create entities
    entities = [
        ProviderSensor(hass, waste_type, data, config) for waste_type in waste_types_provider
    ] + [
        CustomSensor(hass, waste_type, data, config) for waste_type in waste_types_custom
    ]

    if not entities:
        _LOGGER.error("No entities created; check configuration or collector output.")
        return

    _LOGGER.info(f"Adding {len(entities)} sensors for Container Cleaning.")
    async_add_entities(entities, True)


class ContainerCleaningData:
    """Class to handle fetching and storing Container Cleaning data."""

    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.valid: bool = False
        self.waste_data_with_today: dict = {}
        self.waste_data_without_today: dict = {}
        self.waste_data_custom: dict = {}

    def update(self):
        """Fetch the latest waste data."""
        try:
            collector = MainCollector(
                self.config.get(CONF_COLLECTOR),
                self.config.get(CONF_POSTAL_CODE),
                self.config.get(CONF_STREET_NUMBER),
                self.config.get(CONF_SUFFIX),
                self.config.get(CONF_EXCLUDE_PICKUP_TODAY),
                self.config.get(CONF_DATE_ISOFORMAT),
                self.config.get(CONF_EXCLUDE_LIST),
                self.config.get(CONF_DEFAULT_LABEL),
            )
        except ValueError as err:
            _LOGGER.error(f"Waste collector initialization failed: {err}")
            return

        try:
            self.waste_data_with_today = collector.waste_data_with_today
            self.waste_data_without_today = collector.waste_data_without_today
            self.waste_data_custom = collector.waste_data_custom
            self.valid = True
            _LOGGER.debug("Waste data updated successfully.")
        except ValueError as err:
            _LOGGER.error(f"Failed to fetch waste data: {err}")
            self.valid = False
            self.waste_data_with_today = {}
            self.waste_data_without_today = {}
            self.waste_data_custom = {}

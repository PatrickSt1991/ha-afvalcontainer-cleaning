from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .collector.collector import MainCollector
from .const.const import (
    DOMAIN,
    _LOGGER,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_EXCLUDE_PICKUP_TODAY,
    CONF_DATE_ISOFORMAT,
    CONF_EXCLUDE_LIST,
    CONF_DEFAULT_LABEL,
    SCAN_INTERVAL,
)


class ContainerCleaningCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches all container cleaning data once per interval."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.config = config

    async def _async_update_data(self) -> dict:
        _LOGGER.debug("Fetching container cleaning data from provider")
        try:
            data = await self.hass.async_add_executor_job(self._fetch)
            _LOGGER.debug(
                "Fetched %d provider waste types and %d custom sensors",
                len(data["waste_data_with_today"]),
                len(data["waste_data_custom"]),
            )
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching container cleaning data: {err}") from err

    def _fetch(self) -> dict:
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
        return {
            "waste_data_with_today": collector.waste_data_with_today,
            "waste_data_without_today": collector.waste_data_without_today,
            "waste_data_custom": collector.waste_data_custom,
        }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ContainerCleaningCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
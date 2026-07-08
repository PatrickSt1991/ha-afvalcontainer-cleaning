from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from datetime import datetime, timezone

from .collector.collector import MainCollector
from .const.const import (
    DOMAIN,
    _LOGGER,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_EXCLUDE_PICKUP_TODAY,
    CONF_EXCLUDE_LIST,
    CONF_POLL_INTERVAL_HOURS,
    DEFAULT_POLL_INTERVAL_HOURS,
    SCAN_INTERVAL,
)


class ContainerCleaningCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches all container cleaning data once per interval."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        poll_interval_hours = int(config.get(CONF_POLL_INTERVAL_HOURS, DEFAULT_POLL_INTERVAL_HOURS))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=poll_interval_hours) if poll_interval_hours > 0 else SCAN_INTERVAL,
        )
        self.config = config

    async def _async_update_data(self) -> dict:
        _LOGGER.debug("Fetching container cleaning data from provider")
        try:
            data = await self.hass.async_add_executor_job(self._fetch)
            data["last_server_update"] = datetime.now(timezone.utc)
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
            str(self.config.get(CONF_COLLECTOR, "")),
            {
                CONF_POSTAL_CODE: self.config.get(CONF_POSTAL_CODE),
                CONF_STREET_NUMBER: self.config.get(CONF_STREET_NUMBER),
                CONF_SUFFIX: self.config.get(CONF_SUFFIX),
            },
            self.config.get(CONF_EXCLUDE_PICKUP_TODAY),
            str(self.config.get(CONF_EXCLUDE_LIST, "")),
        )
        return {
            "waste_data_with_today": collector.waste_data_with_today,
            "waste_data_without_today": collector.waste_data_without_today,
            "waste_data_custom": collector.waste_data_custom,
        }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


def _is_broken_or_generic_sensor_name(custom_name: str | None, original_name: str | None) -> bool:
    """Return True if an entity name is missing/blank or stuck on generic fallback."""
    if custom_name is None and original_name is None:
        return True

    normalized_custom_name = custom_name.strip().casefold() if isinstance(custom_name, str) else ""
    normalized_original_name = original_name.strip().casefold() if isinstance(original_name, str) else ""
    bad_names = {"", "container cleaning"}

    return normalized_custom_name in bad_names or normalized_original_name in bad_names


async def _async_migrate_broken_entity_names(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove broken/generic entity registry entries so HA can recreate them correctly."""
    registry = er.async_get(hass)
    registry_entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    removed = 0
    for registry_entry in registry_entries:
        if registry_entry.domain != "sensor" or registry_entry.platform != DOMAIN:
            continue

        if _is_broken_or_generic_sensor_name(
            registry_entry.name,
            registry_entry.original_name,
        ):
            registry.async_remove(registry_entry.entity_id)
            removed += 1

    if removed:
        _LOGGER.info(
            "Removed %d broken entity registry entries for %s; they will be recreated with translated names",
            removed,
            DOMAIN,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.title.strip().casefold() in {"", DOMAIN}:
        hass.config_entries.async_update_entry(entry, title="Container Cleaning")

    await _async_migrate_broken_entity_names(hass, entry)

    merged_config = {**entry.data, **entry.options}

    coordinator = ContainerCleaningCoordinator(hass, merged_config)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
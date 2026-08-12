#!/usr/bin/env python3
from datetime import date, datetime, timedelta
import hashlib

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const.const import (
    CONF_ID,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    DOMAIN,
    _LOGGER,
)


def _format_sensor_name(raw_value: str) -> str:
    """Return a human-friendly fallback name for waste types."""
    acronyms = {"gft", "pmd"}
    parts = raw_value.replace("-", " ").replace("_", " ").split()
    formatted = [part.upper() if part.casefold() in acronyms else part.capitalize() for part in parts]
    return " ".join(formatted)


def _provider_display_name(provider: str) -> str:
    """Return a human-friendly provider display name."""
    mapping = {
        "cleanprofs": "CleanProfs",
    }
    provider_key = provider.strip().lower()
    if provider_key in mapping:
        return mapping[provider_key]
    return provider.strip().title() if provider.strip() else "Container Cleaning"


class ContainerCleaningCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity listing every known container pickup for one address."""

    _attr_has_entity_name = True
    _attr_translation_key = "cleaning_schedule"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, config):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self.config = config
        self._collector = str(config.get(CONF_COLLECTOR, "")).strip().lower()
        self._postal_code = str(config.get(CONF_POSTAL_CODE, "")).strip().upper()
        self._street_number = str(config.get(CONF_STREET_NUMBER, "")).strip()
        self._suffix = str(config.get(CONF_SUFFIX, "")).strip().lower()
        self._device_key = f"{self._collector}:{self._postal_code}:{self._street_number}:{self._suffix}"
        self._unique_id = hashlib.sha1(
            (
                f"calendar{config.get(CONF_ID)}{config.get(CONF_COLLECTOR)}"
                f"{config.get(CONF_POSTAL_CODE)}{config.get(CONF_STREET_NUMBER)}"
                f"{config.get(CONF_SUFFIX, '')}"
            ).encode("utf-8")
        ).hexdigest()

    @property
    def unique_id(self):
        """Return a unique ID for the calendar."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata so this calendar groups with the address's sensors."""
        provider_name = _provider_display_name(self._collector)
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name=provider_name,
            manufacturer="Container Cleaning",
            model=provider_name,
        )

    def _get_waste_events(self):
        """Return the raw waste event list from the coordinator, or an empty list."""
        if self.coordinator.data is None:
            return []
        return self.coordinator.data.get("waste_data_events", [])

    @staticmethod
    def _to_calendar_event(item) -> CalendarEvent:
        """Convert a single {type, date} waste item into an all-day CalendarEvent."""
        start = item["date"].date()
        return CalendarEvent(
            start=start,
            end=start + timedelta(days=1),
            summary=_format_sensor_name(item["type"]),
        )

    @property
    def event(self):
        """Return the soonest upcoming (or today's) pickup, or None."""
        today = date.today()
        upcoming = sorted(
            (item for item in self._get_waste_events() if item["date"].date() >= today),
            key=lambda item: item["date"],
        )
        if not upcoming:
            return None
        return self._to_calendar_event(upcoming[0])

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime):
        """Return all pickups within [start_date, end_date)."""
        range_start = start_date.date()
        range_end = end_date.date()
        return [
            self._to_calendar_event(item)
            for item in self._get_waste_events()
            if range_start <= item["date"].date() < range_end
        ]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the calendar entity from a config entry using the shared coordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data is None:
        _LOGGER.warning("No data available from coordinator; calendar cannot be created.")
        return

    async_add_entities([ContainerCleaningCalendar(coordinator, entry.data)])

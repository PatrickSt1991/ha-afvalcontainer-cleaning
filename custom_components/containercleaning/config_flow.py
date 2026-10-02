import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .collector import manual
from .const.const import (
    DOMAIN,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_EXCLUDE_PICKUP_TODAY,
    CONF_DATE_ISOFORMAT,
    CONF_EXCLUDE_LIST,
    CONF_FILE_PATH,
    CONF_POLL_INTERVAL_HOURS,
    DEFAULT_MANUAL_FILE_PATH,
    DEFAULT_POLL_INTERVAL_HOURS,
    SENSOR_COLLECTORS_CLEANPROFS,
    SENSOR_COLLECTORS_MANUAL,
)


collectors = sorted(
    set(
        list(SENSOR_COLLECTORS_CLEANPROFS.keys())
        + list(SENSOR_COLLECTORS_MANUAL.keys())
    )
)

PROVIDER_SCHEMA = vol.Schema({
    vol.Required(CONF_COLLECTOR): vol.In(collectors),
})

COMMON_OPTIONS_SCHEMA = {
    vol.Optional(CONF_EXCLUDE_PICKUP_TODAY, default=True): cv.boolean,
    vol.Optional(CONF_DATE_ISOFORMAT, default=False): cv.boolean,
    vol.Optional(CONF_EXCLUDE_LIST, default=""): cv.string,
}

ADDRESS_SCHEMA = vol.Schema({
    vol.Required(CONF_POSTAL_CODE): cv.string,
    vol.Required(CONF_STREET_NUMBER): cv.string,
    vol.Optional(CONF_SUFFIX, default=""): cv.string,
    **COMMON_OPTIONS_SCHEMA,
})

MANUAL_SCHEMA = vol.Schema({
    vol.Optional(CONF_FILE_PATH, default=DEFAULT_MANUAL_FILE_PATH): cv.string,
    **COMMON_OPTIONS_SCHEMA,
})


def _is_supported_source(source: str) -> bool:
    """Accept a JSON file, an iCalendar file, or an http(s) URL."""
    return (
        manual.is_url(source)
        or manual.is_ical_path(source)
        or source.strip().lower().endswith(".json")
    )


class ContainerCleaningConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._provider: str = ""

    @staticmethod
    def async_get_options_flow(config_entry):
        return ContainerCleaningOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """First step: pick the provider, then branch to the matching details step."""
        if user_input is not None:
            self._provider = str(user_input.get(CONF_COLLECTOR, "")).strip().lower()
            if self._provider in SENSOR_COLLECTORS_MANUAL:
                return await self.async_step_manual()
            return await self.async_step_address()

        return self.async_show_form(
            step_id="user",
            data_schema=PROVIDER_SCHEMA,
        )

    async def async_step_address(self, user_input=None):
        """Address details for API-based providers."""
        errors = {}

        if user_input is not None:
            if not self._validate_postal_code(user_input.get(CONF_POSTAL_CODE)):
                errors["postal_code"] = "invalid_postal_code"
            elif not self._validate_street_number(user_input.get(CONF_STREET_NUMBER)):
                errors["street_number"] = "invalid_street_number"
            else:
                return self.async_create_entry(
                    title="Container Cleaning",
                    data=self._build_entry_data(user_input),
                )

        return self.async_show_form(
            step_id="address",
            data_schema=ADDRESS_SCHEMA,
            errors=errors,
        )

    async def async_step_manual(self, user_input=None):
        """File location for the manual date file provider."""
        errors = {}

        if user_input is not None:
            file_path = str(user_input.get(CONF_FILE_PATH, "")).strip() or DEFAULT_MANUAL_FILE_PATH
            if not _is_supported_source(file_path):
                errors["file_path"] = "invalid_file_path"
            else:
                user_input[CONF_FILE_PATH] = file_path
                return self.async_create_entry(
                    title="Container Cleaning",
                    data=self._build_entry_data(user_input),
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=MANUAL_SCHEMA,
            errors=errors,
        )

    def _build_entry_data(self, user_input: dict) -> dict:
        data = {
            CONF_COLLECTOR: self._provider,
            CONF_POSTAL_CODE: "",
            CONF_STREET_NUMBER: "",
            CONF_SUFFIX: "",
            **user_input,
        }
        data[CONF_EXCLUDE_LIST] = str(data.get(CONF_EXCLUDE_LIST, "")).lower()
        return data

    def _validate_postal_code(self, postal_code):
        return (
            isinstance(postal_code, str)
            and len(postal_code) == 6
            and postal_code[:4].isdigit()
            and postal_code[4:].isalpha()
        )

    def _validate_street_number(self, street_number):
        return isinstance(street_number, str) and street_number.isdigit()


class ContainerCleaningOptionsFlow(config_entries.OptionsFlow):
    """Handle Container Cleaning options."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    def _current(self, key, default):
        return self._config_entry.options.get(key, self._config_entry.data.get(key, default))

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if CONF_FILE_PATH in user_input:
                user_input[CONF_FILE_PATH] = (
                    str(user_input[CONF_FILE_PATH]).strip() or DEFAULT_MANUAL_FILE_PATH
                )
                if not _is_supported_source(user_input[CONF_FILE_PATH]):
                    errors["file_path"] = "invalid_file_path"
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        schema = {}

        provider = str(self._config_entry.data.get(CONF_COLLECTOR, "")).strip().lower()
        if provider in SENSOR_COLLECTORS_MANUAL:
            schema[vol.Optional(
                CONF_FILE_PATH,
                default=self._current(CONF_FILE_PATH, DEFAULT_MANUAL_FILE_PATH),
            )] = cv.string

        schema.update(
            {
                vol.Optional(
                    CONF_EXCLUDE_PICKUP_TODAY,
                    default=self._current(CONF_EXCLUDE_PICKUP_TODAY, True),
                ): cv.boolean,
                vol.Optional(
                    CONF_DATE_ISOFORMAT,
                    default=self._current(CONF_DATE_ISOFORMAT, False),
                ): cv.boolean,
                vol.Optional(
                    CONF_EXCLUDE_LIST,
                    default=self._current(CONF_EXCLUDE_LIST, ""),
                ): cv.string,
                vol.Optional(
                    CONF_POLL_INTERVAL_HOURS,
                    default=self._config_entry.options.get(
                        CONF_POLL_INTERVAL_HOURS,
                        DEFAULT_POLL_INTERVAL_HOURS,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

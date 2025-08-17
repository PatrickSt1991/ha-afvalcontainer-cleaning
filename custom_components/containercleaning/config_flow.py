import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
import logging

from .const.const import (
    DOMAIN,
    _LOGGER,
    CONF_COLLECTOR,
    CONF_POSTAL_CODE,
    CONF_STREET_NUMBER,
    CONF_SUFFIX,
    CONF_EXCLUDE_PICKUP_TODAY,
    CONF_DATE_ISOFORMAT,
    CONF_DEFAULT_LABEL,
    CONF_EXCLUDE_LIST,
    SENSOR_COLLECTORS_CLEANPROFS,
)


collectors = sorted(
    set(
        list(SENSOR_COLLECTORS_CLEANPROFS.keys())
    )
)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_COLLECTOR): vol.In(collectors),
    vol.Required(CONF_POSTAL_CODE): cv.string,
    vol.Required(CONF_STREET_NUMBER): cv.string,
    vol.Optional(CONF_SUFFIX, default=""): cv.string,
    vol.Optional(CONF_EXCLUDE_PICKUP_TODAY, default=True): cv.boolean,
    vol.Optional(CONF_DATE_ISOFORMAT, default=False): cv.boolean,
    vol.Optional(CONF_DEFAULT_LABEL, default="geen"): cv.string,
    vol.Optional(CONF_EXCLUDE_LIST, default=""): cv.string,
})

_LOGGER = logging.getLogger(__name__)

class ContainerCleaningConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            user_input[CONF_COLLECTOR] = user_input.get(CONF_COLLECTOR, "").lower()
            user_input[CONF_EXCLUDE_LIST] = user_input.get(CONF_EXCLUDE_LIST, "").lower()

            if not self._validate_postal_code(user_input.get(CONF_POSTAL_CODE)):
                errors["postal_code"] = "config.error.invalid_postal_code"
            elif not self._validate_street_number(user_input.get(CONF_STREET_NUMBER)):
                errors["street_number"] = "config.error.invalid_street_number"
            else:
                return self.async_create_entry(title="containercleaning", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={},
        )

    def _validate_postal_code(self, postal_code):
        return (
            isinstance(postal_code, str)
            and len(postal_code) == 6
            and postal_code[:4].isdigit()
            and postal_code[4:].isalpha()
        )

    def _validate_street_number(self, street_number):
        return street_number.isdigit()
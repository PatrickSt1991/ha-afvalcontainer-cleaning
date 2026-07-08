from ..common.main_functions import normalize_bool_param
from ..common.waste_data_transformer import WasteDataTransformer
from ..const.const import (
    _LOGGER,
    SENSOR_COLLECTORS_CLEANPROFS
)

from . import cleanprofs

class MainCollector:
    """
    MainCollector collects and transforms waste data from various providers.
    """

    def __init__(
        self,
        provider: str,
        address: dict,
        exclude_pickup_today,
        exclude_list: str,
    ):
        # Normalize input parameters
        self.provider = str(provider).strip().lower()
        self.postal_code = str(address.get("postal_code", "")).strip().upper()
        self.street_number = str(address.get("street_number", "")).strip()
        self.suffix = str(address.get("suffix", "")).strip().lower()

        self.exclude_pickup_today = normalize_bool_param(exclude_pickup_today)
        self.exclude_list = str(exclude_list).strip().lower()

        waste_data_raw = self._get_waste_data_raw()

        if not isinstance(waste_data_raw, list):
            raise ValueError(
                f"No valid waste data received from provider '{self.provider}'. "
                "Check your postal code, street number, and provider configuration."
            )

        # Transform raw waste data
        self._waste_data = WasteDataTransformer(
            waste_data_raw,
            self.exclude_pickup_today,
            self.exclude_list,
        )

    def _get_waste_data_raw(self):
        """
        Determines the correct provider module to call based on the provider and retrieves raw waste data.
        """
        try:
            # List of providers with common parameter signatures
            common_providers = [
                (SENSOR_COLLECTORS_CLEANPROFS, cleanprofs.get_waste_data_raw)
            ]
            for sensor_set, getter in common_providers:
                keys = sensor_set.keys() if isinstance(sensor_set, dict) else sensor_set
                if self.provider in keys:
                    _LOGGER.debug("Using provider '%s'", self.provider)
                    return getter(self.provider, self.postal_code, self.street_number, self.suffix)

            _LOGGER.error("Unknown provider '%s' — check your integration configuration", self.provider)
            raise ValueError(f"Unknown provider: {self.provider}")

        except ValueError:
            raise

    @property
    def waste_data_with_today(self):
        return self._waste_data.waste_data_with_today

    @property
    def waste_data_without_today(self):
        return self._waste_data.waste_data_without_today

    @property
    def waste_data_provider(self):
        return self._waste_data.waste_data_provider

    @property
    def waste_types_provider(self):
        return self._waste_data.waste_types_provider

    @property
    def waste_data_custom(self):
        return self._waste_data.waste_data_custom

    @property
    def waste_types_custom(self):
        return self._waste_data.waste_types_custom
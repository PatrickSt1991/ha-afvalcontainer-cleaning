from ..common.main_functions import normalize_bool_param
from ..common.waste_data_transformer import WasteDataTransformer
from ..const.const import (
    _LOGGER,
    SENSOR_COLLECTORS_CLEANPROFS
)

try:
    from . import cleanprofs
except ImportError as err:
    _LOGGER.error(f"Import error {err.args}")

class MainCollector:
    """
    MainCollector collects and transforms waste data from various providers.
    """

    def __init__(
        self,
        provider: str,
        postal_code: str,
        street_number: str,
        suffix: str,
        exclude_pickup_today,
        date_isoformat,
        exclude_list: str,
        default_label: str,
    ):
        # Normalize input parameters
        self.provider = str(provider).strip().lower()
        self.postal_code = str(postal_code).strip().upper()
        self.street_number = str(street_number).strip()
        self.suffix = str(suffix).strip().lower()

        self.exclude_pickup_today = normalize_bool_param(exclude_pickup_today)
        self.date_isoformat = normalize_bool_param(date_isoformat)
        self.exclude_list = str(exclude_list).strip().lower()
        self.default_label = str(default_label).strip()

        waste_data_raw = self._get_waste_data_raw()

        # Transform raw waste data
        self._waste_data = WasteDataTransformer(
            waste_data_raw,
            self.exclude_pickup_today,
            self.exclude_list,
            self.default_label,
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
                    return getter(self.provider, self.postal_code, self.street_number, self.suffix)

            _LOGGER.error(f"Unknown provider: {self.provider}")
            raise ValueError(f"Unknown provider: {self.provider}")

        except ValueError as err:
            _LOGGER.error(f"Check platform settings: {err}")
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
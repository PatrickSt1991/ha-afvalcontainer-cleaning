from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

API = "api"
NAME = "containercleaning"
VERSION = "2025.08.17"

ISSUE_URL = "https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/issues"

SENSOR_COLLECTORS_CLEANPROFS = {
    "cleanprofs": "https://cleanprofs.jmsdev.nl/api/get-plannings-address?zipcode={0}&house_number={1}&suffix={2}",
}

CONF_COLLECTOR = "provider"
CONF_POSTAL_CODE = "postal_code"
CONF_STREET_NUMBER = "street_number"
CONF_SUFFIX = "suffix"
CONF_DATE_FORMAT = "date_format"
CONF_EXCLUDE_PICKUP_TODAY = "exclude_pickup_today"
CONF_DEFAULT_LABEL = "default_label"
CONF_ID = "id"
CONF_EXCLUDE_LIST = "exclude_list"
CONF_DATE_ISOFORMAT = "date_isoformat"

SENSOR_PREFIX = "containercleaning "
SENSOR_ICON = "mdi:delete-circle-outline"

ATTR_LAST_UPDATE = "last_update"
ATTR_IS_COLLECTION_DATE_TODAY = "is_collection_date_today"
ATTR_IS_COLLECTION_DATE_TOMORROW = "is_collection_date_tomorrow"
ATTR_IS_COLLECTION_DATE_DAY_AFTER_TOMORROW = "is_collection_date_day_after_tomorrow"
ATTR_DAYS_UNTIL_COLLECTION_DATE = "days_until_collection_date"

SCAN_INTERVAL = timedelta(hours=4)

DOMAIN = "containercleaning"
DOMAIN_DATA = "containercleaning_data"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------,
Container Cleaning - {VERSION},
This is a custom integration!,
If you have any issues with this you need to open an issue here:,
https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/issues,
-------------------------------------------------------------------,
"""
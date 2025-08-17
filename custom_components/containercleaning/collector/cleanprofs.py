from ..const.const import _LOGGER, SENSOR_COLLECTORS_CLEANPROFS
from ..common.main_functions import waste_type_rename
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_waste_data_raw(provider, postal_code, street_number, suffix):
    if provider not in SENSOR_COLLECTORS_CLEANPROFS:
        raise ValueError(f"Invalid provider: {provider}, please verify")

    try:
        url = SENSOR_COLLECTORS_CLEANPROFS[provider].format(postal_code, street_number, suffix)
        raw_response = requests.get(url, timeout=60, verify=False)

        if not raw_response.ok:
            raise ValueError(f"Endpoint {url} returned status {raw_response.status_code}")

        try:
            response = raw_response.json()
        except ValueError as err:
            raise ValueError(f"Invalid and/or no JSON data received from {url}") from err

        if response == []:
            raise ValueError(f"Endpoint {url} returned an empty array, no data available for {postal_code} {street_number} {suffix}")

    except (requests.exceptions.RequestException, ValueError) as err:
        _LOGGER.error(f"Error fetching data from API: {err}")
        return False

    waste_data_raw = []
    try:
        for item in response:
            if not item['full_date']:
                continue
            waste_type = waste_type_rename(item['product_name'].strip().lower())
            if not waste_type:
                continue
            waste_data_raw.append({"type": waste_type, "date": item['full_date']})

    except Exception as exc:
        _LOGGER.error('Error occurred while processing data: %r', exc)
        return False

    return waste_data_raw

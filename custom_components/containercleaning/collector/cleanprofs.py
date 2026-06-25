from ..const.const import _LOGGER, SENSOR_COLLECTORS_CLEANPROFS
from ..common.main_functions import waste_type_rename
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _make_session() -> requests.Session:
    """Create a requests Session with exponential backoff retry on transient errors."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,          # waits 0 s, 1 s, 2 s between attempts
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,     # we check status ourselves below
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_waste_data_raw(provider, postal_code, street_number, suffix):
    if provider not in SENSOR_COLLECTORS_CLEANPROFS:
        raise ValueError(f"Invalid provider: {provider}, please verify")

    session = _make_session()
    try:
        url = SENSOR_COLLECTORS_CLEANPROFS[provider].format(postal_code, street_number, suffix)
        _LOGGER.debug("Requesting cleaning schedule from %s", url)
        raw_response = session.get(url, timeout=15, verify=False)

        if not raw_response.ok:
            raise ValueError(f"Endpoint {url} returned status {raw_response.status_code}")

        try:
            response = raw_response.json()
        except ValueError as err:
            raise ValueError(f"Invalid and/or no JSON data received from {url}") from err

        if response == []:
            raise ValueError(f"Endpoint {url} returned an empty array, no data available for {postal_code} {street_number} {suffix}")

        _LOGGER.debug("Received %d raw records from provider", len(response))

    except requests.exceptions.RequestException as err:
        _LOGGER.error("Network error fetching data from API (all retries exhausted): %s", err)
        return False
    except ValueError as err:
        _LOGGER.error("Data error from API: %s", err)
        return False
    finally:
        session.close()

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
        _LOGGER.warning("Error occurred while processing raw API data: %r", exc)
        return False

    _LOGGER.debug("Parsed %d cleaning schedule entries", len(waste_data_raw))
    return waste_data_raw

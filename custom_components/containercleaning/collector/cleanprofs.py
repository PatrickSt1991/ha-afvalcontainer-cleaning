from ..const.const import _LOGGER, SENSOR_COLLECTORS_CLEANPROFS
from ..common.main_functions import waste_type_rename
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    """Return a lazily initialized shared HTTP session."""
    global _SESSION
    if _SESSION is None:
        _SESSION = _make_session()
    return _SESSION


def close_session() -> None:
    """Close and clear the shared HTTP session."""
    global _SESSION
    if _SESSION is not None:
        _SESSION.close()
        _SESSION = None


def get_waste_data_raw(provider, postal_code, street_number, suffix):
    if provider not in SENSOR_COLLECTORS_CLEANPROFS:
        raise ValueError(f"Invalid provider: {provider}, please verify")

    session = _get_session()
    try:
        url = SENSOR_COLLECTORS_CLEANPROFS[provider].format(postal_code, street_number, suffix)
        _LOGGER.debug("Requesting cleaning schedule from provider '%s'", provider)
        raw_response = session.get(url, timeout=15)

        if not raw_response.ok:
            raise ValueError(f"Provider endpoint returned status {raw_response.status_code}")

        try:
            response = raw_response.json()
        except ValueError as err:
            raise ValueError("Invalid and/or no JSON data received from provider") from err

        if response == []:
            raise ValueError("Provider returned an empty array, no cleaning data available")

        _LOGGER.debug("Received %d raw records from provider", len(response))

    except requests.exceptions.RequestException as err:
        _LOGGER.warning("Network error fetching data from provider API (all retries exhausted): %s", err)
        return False
    except ValueError as err:
        _LOGGER.warning("Data error from provider API: %s", err)
        return False

    waste_data_raw = []
    try:
        for item in response:
            if not item['full_date']:
                continue
            waste_type = waste_type_rename(item['product_name'].strip().lower())
            if not waste_type:
                continue

            parsed_date = datetime.strptime(item["full_date"], "%Y-%m-%d")
            waste_data_raw.append({"type": waste_type, "date": parsed_date})

    except Exception:
        _LOGGER.exception("Unexpected error while processing raw API data")
        return False

    _LOGGER.debug("Parsed %d cleaning schedule entries", len(waste_data_raw))
    return waste_data_raw

"""Manual date file provider.

Reads cleaning dates from a user-maintained source so services without a
public API (for example VCCS) can still be tracked. The source can be:

* a local JSON file,
* a local iCalendar (.ics) file, as downloaded from the cleaning service,
* an http(s) URL pointing at an iCalendar feed or a JSON document.

Relative paths are resolved against the Home Assistant config directory.

Supported JSON layouts:

1. A list of entries::

    [
      {"type": "gft", "date": "2026-10-15"},
      {"type": "restafval", "date": "15-10-2026"}
    ]

2. A mapping of container type to a list of dates::

    {
      "gft": ["2026-10-15", "2026-11-12"],
      "restafval": ["2026-10-15"]
    }

Both layouts may also be wrapped in an object under a ``cleanings`` key.
Dates are accepted as ``YYYY-MM-DD`` or ``DD-MM-YYYY``.

For iCalendar input every ``VEVENT`` becomes one cleaning: ``DTSTART`` is the
date and the container type is derived from ``SUMMARY`` (a known container type
such as ``gft`` or ``restafval`` is picked out of the summary when present).
"""

import json
import os
import re
from datetime import datetime

import requests

from ..common.main_functions import waste_type_rename
from ..const.const import _LOGGER, SENSOR_COLLECTORS_MANUAL

DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y")

# Canonical container types the integration knows icons/translations for.
KNOWN_WASTE_TYPES = (
    "best-tas",
    "chemisch",
    "gft",
    "glas",
    "grofvuil",
    "kerstbomen",
    "papier",
    "plastic",
    "pmd-restafval",
    "pmd",
    "restafvalzakken",
    "restafval",
    "restwagen",
    "snoeiafval",
    "takken",
    "textiel",
    "tuinafval",
)

EXAMPLE_FILE_CONTENT = {
    "cleanings": [
        {"type": "gft", "date": "2026-01-15"},
        {"type": "restafval", "date": "2026-01-15"},
    ]
}

_ICS_LINE_SPLIT = re.compile(r"\r?\n")
_NON_WORD = re.compile(r"[^a-z0-9]+")


def is_url(source: str) -> bool:
    return str(source).strip().lower().startswith(("http://", "https://"))


def is_ical_path(source: str) -> bool:
    return str(source).strip().lower().endswith((".ics", ".ical", ".ifb", ".icalendar"))


def _parse_date(raw_date) -> datetime | None:
    """Parse a date string using the supported formats, returning None if invalid."""
    if not isinstance(raw_date, str):
        return None
    value = raw_date.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def _iter_json_entries(payload):
    """Yield (type, raw_date) tuples from any of the supported JSON layouts."""
    if isinstance(payload, dict) and "cleanings" in payload:
        payload = payload["cleanings"]

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                _LOGGER.warning("Skipping manual entry that is not an object: %r", item)
                continue
            yield item.get("type"), item.get("date")
        return

    if isinstance(payload, dict):
        for waste_type, dates in payload.items():
            if isinstance(dates, str):
                dates = [dates]
            if not isinstance(dates, list):
                _LOGGER.warning("Skipping manual type '%s': dates must be a list", waste_type)
                continue
            for raw_date in dates:
                yield waste_type, raw_date
        return

    raise ValueError("Manual date file must contain a JSON list or object")


def _parse_json(text: str) -> list:
    payload = json.loads(text)
    waste_data_raw = []
    for raw_type, raw_date in _iter_json_entries(payload):
        if not isinstance(raw_type, str) or not raw_type.strip():
            _LOGGER.warning("Skipping manual entry without a container type: %r", raw_date)
            continue

        parsed_date = _parse_date(raw_date)
        if parsed_date is None:
            _LOGGER.warning(
                "Skipping manual entry for '%s': invalid date %r (expected YYYY-MM-DD or DD-MM-YYYY)",
                raw_type,
                raw_date,
            )
            continue

        waste_type = waste_type_rename(raw_type)
        if waste_type:
            waste_data_raw.append({"type": waste_type, "date": parsed_date})
    return waste_data_raw


# ---------------------------------------------------------------------------
# iCalendar
# ---------------------------------------------------------------------------
def _unfold_ical_lines(text: str) -> list[str]:
    """Join folded continuation lines (RFC 5545 §3.1)."""
    lines: list[str] = []
    for raw_line in _ICS_LINE_SPLIT.split(text):
        if not raw_line:
            continue
        if raw_line[0] in (" ", "\t") and lines:
            lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)
    return lines


_BACKSLASH = chr(92)


def _unescape_ical_text(value: str) -> str:
    """Undo RFC 5545 TEXT escaping (backslash-escaped newline, comma, semicolon, backslash)."""
    return (
        value.replace(_BACKSLASH + "n", " ")
        .replace(_BACKSLASH + "N", " ")
        .replace(_BACKSLASH + ",", ",")
        .replace(_BACKSLASH + ";", ";")
        .replace(_BACKSLASH * 2, _BACKSLASH)
    )


def _parse_ical_dtstart(value: str) -> datetime | None:
    """Parse a DTSTART value (DATE or DATE-TIME) to a naive date at midnight."""
    value = value.strip()
    for fmt in ("%Y%m%d", "%Y%m%dT%H%M%S", "%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            continue
    return None


def waste_type_from_summary(summary: str) -> str:
    """Derive a container type from an event summary.

    Known container names inside the summary win (``"Reiniging GFT container"`` -> ``gft``);
    otherwise the whole summary is normalized and used as the type.
    """
    cleaned = summary.strip().lower()
    if not cleaned:
        return ""

    direct = waste_type_rename(cleaned)
    if direct in KNOWN_WASTE_TYPES:
        return direct

    tokens = [token for token in _NON_WORD.split(cleaned) if token]
    for token in tokens:
        renamed = waste_type_rename(token)
        if renamed in KNOWN_WASTE_TYPES:
            return renamed

    for known in KNOWN_WASTE_TYPES:
        if known in cleaned:
            return known

    return _NON_WORD.sub("-", cleaned).strip("-")


def _parse_ical(text: str) -> list:
    waste_data_raw = []
    in_event = False
    dtstart: str | None = None
    summary: str | None = None
    has_rrule = False

    for line in _unfold_ical_lines(text):
        if line.startswith("BEGIN:VEVENT"):
            in_event, dtstart, summary, has_rrule = True, None, None, False
            continue

        if line.startswith("END:VEVENT"):
            in_event = False
            if dtstart is None:
                _LOGGER.warning("Skipping iCal event without DTSTART (summary %r)", summary)
                continue
            parsed_date = _parse_ical_dtstart(dtstart)
            if parsed_date is None:
                _LOGGER.warning("Skipping iCal event with unparsable DTSTART %r", dtstart)
                continue
            waste_type = waste_type_from_summary(summary or "")
            if not waste_type:
                _LOGGER.warning("Skipping iCal event on %s without a summary", parsed_date.date())
                continue
            if has_rrule:
                _LOGGER.warning(
                    "iCal event '%s' on %s has an RRULE; recurrences are not expanded, only the first date is used",
                    waste_type,
                    parsed_date.date(),
                )
            waste_data_raw.append({"type": waste_type, "date": parsed_date})
            continue

        if not in_event or ":" not in line:
            continue

        name_part, value = line.split(":", 1)
        name = name_part.split(";", 1)[0].upper()
        if name == "DTSTART":
            dtstart = value
        elif name == "SUMMARY":
            summary = _unescape_ical_text(value)
        elif name == "RRULE":
            has_rrule = True

    return waste_data_raw


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------
def _looks_like_ical(text: str) -> bool:
    return text.lstrip().upper().startswith("BEGIN:VCALENDAR")


def _load_source(source: str) -> str:
    if is_url(source):
        _LOGGER.debug("Downloading manual cleaning schedule from URL")
        response = requests.get(source, timeout=15)
        if not response.ok:
            raise ValueError(f"URL returned status {response.status_code}")
        return response.text

    with open(source, encoding="utf-8") as handle:
        return handle.read()


def write_example_file(file_path: str) -> bool:
    """Create an example JSON date file if none exists yet. Returns True when a file was written."""
    if is_url(file_path) or is_ical_path(file_path) or os.path.exists(file_path):
        return False

    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(EXAMPLE_FILE_CONTENT, handle, indent=2)
        handle.write("\n")

    _LOGGER.info("Created example manual date file at %s", file_path)
    return True


def get_waste_data_raw(provider, file_path):
    if provider not in SENSOR_COLLECTORS_MANUAL:
        raise ValueError(f"Invalid provider: {provider}, please verify")

    if not file_path:
        raise ValueError("No manual date file path or URL configured")

    try:
        text = _load_source(file_path)
    except FileNotFoundError:
        _LOGGER.warning("Manual date file not found: %s", file_path)
        return False
    except OSError as err:
        _LOGGER.warning("Could not read manual date file %s: %s", file_path, err)
        return False
    except requests.exceptions.RequestException as err:
        _LOGGER.warning("Network error downloading manual cleaning schedule: %s", err)
        return False
    except ValueError as err:
        _LOGGER.warning("Could not download manual cleaning schedule: %s", err)
        return False

    try:
        if _looks_like_ical(text) or (is_ical_path(file_path) and not is_url(file_path)):
            waste_data_raw = _parse_ical(text)
        else:
            waste_data_raw = _parse_json(text)
    except json.JSONDecodeError as err:
        _LOGGER.warning("Manual date source %s is not valid JSON: %s", file_path, err)
        return False
    except ValueError as err:
        _LOGGER.warning("Data error in manual date source %s: %s", file_path, err)
        return False
    except Exception:
        _LOGGER.exception("Unexpected error while processing manual date source")
        return False

    if not waste_data_raw:
        _LOGGER.warning("Manual date source %s contains no usable cleaning dates", file_path)

    _LOGGER.debug("Parsed %d cleaning schedule entries from manual date source", len(waste_data_raw))
    return waste_data_raw

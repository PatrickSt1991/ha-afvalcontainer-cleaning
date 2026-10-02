[![hacs_badge](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/PatrickSt1991/ha-afvalcontainer-cleaning)](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/releases)
[![License](https://img.shields.io/github/license/PatrickSt1991/ha-afvalcontainer-cleaning)](LICENSE)

[![Validate](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/validate.yaml/badge.svg)](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/validate.yaml)
[![CodeQL](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/PatrickSt1991/ha-afvalcontainer-cleaning/actions/workflows/dependabot/dependabot-updates)

# 🧼 Afvalcontainer Cleaning

<img src="https://madebypatrick.nl/assets/ha-cc-CUWVCUA3.svg" alt="clean container" width="400">

A **Home Assistant integration** for monitoring **garbage container cleaning schedules**.  

Need to know when your garbage containers will be cleaned?  
This integration adds **sensors** to Home Assistant that track cleaning services, so you’ll never miss a cleaning appointment again.  

---

## ✨ Features
- Adds `sensor.cleaningcontainer_*` entities in Home Assistant.  
- Tracks upcoming container cleaning schedules.  
- Supports multiple providers (see below).  
- Supports a **manual date file** (JSON or iCal `.ics`, local file or URL) for cleaning services without an API, such as VCCS.  
- Uses context-aware icons for provider and summary sensors to improve dashboard readability.
- Includes a diagnostic sensor for the last successful server update timestamp.
- Uses a clear integration title (`Container Cleaning`) and provider-based device names (for example `CleanProfs`).
- Lets you configure the server poll interval from integration settings (1-24 hours).
- Uses privacy-conscious logging (no address details in normal logs) and warning-level messages for expected provider fetch issues.
- Enforces HTTPS/TLS certificate validation for provider API requests.
- Uses exact comma-separated exclude matching (for example `paper,plastic`) to reduce false matches and processing overhead.
- Reuses a persistent HTTP session for provider polling to reduce connection setup overhead.
- Parses provider dates once and carries datetime values through transformation to avoid repeated parsing work.
- Built with inspiration from [@xirixiz/homeassistant-afvalwijzer](https://github.com/xirixiz/homeassistant-afvalwijzer), but focused on **cleaning services** instead of **garbage collection**.

---

## 📦 Supported Providers
Currently, the integration supports the following providers/communities:

| Provider   | Source |
|------------|--------|
| **cleanprofs** | CleanProfs API (postal code + house number) |
| **manual** | Your own JSON or iCal (`.ics`) file, or an iCal URL — for services without an API (for example VCCS) |

> ⚠️ Availability depends on whether your municipality or service provider is supported and/or can be added.
> If your service has no API but lets you download an iCal/ICS calendar, use the **manual** provider.

---

## 🚀 Installation

### Installation via HACS

1. Ensure HACS is installed in your Home Assistant setup. If not, follow
   the [HACS installation guide](https://hacs.xyz/docs/setup/download).
2. Open the HACS panel in Home Assistant.
3. Click on the `Frontend` or `Integrations` tab.
4. Click the `+` button and search for `Afvalwijzer`.
5. Click `Install` to add the component to your Home Assistant setup.
6. Restart Home Assistant after the installation completes.

### Manual Installation
1. Download or clone this repository.  
2. Copy the `custom_components/containercleaning` folder into your Home Assistant `custom_components` directory.  
   - Example: `/config/custom_components/containercleaning/`  
3. Restart Home Assistant.  

---

## ⚙️ Configuration

You can configure the integration either via the **UI** (recommended) or with `configuration.yaml`.  

### Option 1: UI Configuration
1. Go to **Settings → Devices & Services → Integrations**.  
2. Click **Add Integration**.  
3. Search for **Container Cleaning** and follow the setup wizard.  
4. Pick a provider. For `cleanprofs` you enter your address; for `manual` you point the integration at a date file or URL (see below).  

### Option 2: Manual date file (JSON or iCal)

Use the **manual** provider when your cleaning service (for example **VCCS**) has no public API. You maintain the dates yourself, or let the integration read an iCal calendar the service lets you download.

The *File path or URL* field accepts:

| Value | Behaviour |
|-------|-----------|
| `containercleaning/cleaning_dates.json` (default) | JSON file relative to your Home Assistant config directory. If it does not exist yet, an example file is created for you to edit. |
| `containercleaning/vccs.ics` | An iCalendar file you downloaded from your cleaning service and placed in the config directory. |
| `https://example.com/calendar.ics` | An iCal (or JSON) URL that is downloaded every poll interval, so updates arrive automatically. |
| `/media/cleaning.json` | An absolute path. Paths outside the config directory must be listed in `allowlist_external_dirs`. |

**JSON format** — either a list of entries or a mapping per container type (both may be wrapped in a `cleanings` key). Dates are `YYYY-MM-DD` or `DD-MM-YYYY`:

```json
{
  "cleanings": [
    { "type": "gft", "date": "2026-10-15" },
    { "type": "restafval", "date": "15-10-2026" }
  ]
}
```

```json
{
  "gft": ["2026-10-15", "2026-11-12"],
  "restafval": ["2026-10-15"]
}
```

**iCal format** — every `VEVENT` becomes a cleaning. `DTSTART` is the date and the container type is taken from `SUMMARY`: a known type inside the summary wins (for example `Reiniging GFT container` → `gft`, `Containerreiniging restafval` → `restafval`); otherwise the whole summary is used as the type. Recurring events (`RRULE`) are not expanded, only their first date is used.

Container types use the same names as the API providers (`gft`, `restafval`, `pmd`, `papier`, `plastic`, `glas`, …), so the same sensors, icons and translations apply. Unknown names simply become their own sensor.

The file is re-read every poll interval (default 4 hours). After editing it you can also reload the integration from **Settings → Devices & Services** to apply changes immediately. The file path or URL can be changed later via the integration's **Configure** dialog.

When no cleaning date is available, sensors no longer use a custom fallback label. Home Assistant now shows its built-in translated unknown/unavailable state.

Entity names now use Home Assistant translations. If older entities were created while running a previous naming scheme, the integration performs an automatic one-time registry migration and recreates only broken nameless sensor entries.


---

🛠️ Created Sensors

Once configured, the following sensors are available:

sensor.cleaningcontainer_next → Date of next scheduled cleaning

sensor.cleaningcontainer_days_until → Days until the next cleaning

sensor.cleaningcontainer_last_update → Last time data was updated



---

📊 Example Lovelace Card

Here’s an example Entities card to display the sensors in your dashboard:

type: entities
title: Container Cleaning
entities:
  - entity: sensor.cleaningcontainer_next
    name: Next Cleaning
  - entity: sensor.cleaningcontainer_days_until
    name: Days Remaining
  - entity: sensor.cleaningcontainer_last_update
    name: Last Update

You can also use these sensors in automations (e.g., to send reminders before cleaning day).


---

🙌 Credits

Forked from [homeassistant-afvalwijzer by @xirixiz](https://github.com/xirixiz/homeassistant-afvalwijzer).
Adapted to focus on container cleaning services.


---

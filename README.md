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
- Uses context-aware icons for provider and summary sensors to improve dashboard readability.
- Includes a diagnostic sensor for the last successful server update timestamp.
- Uses a clear integration title (`Container Cleaning`) and provider-based device names (for example `CleanProfs`).
- Lets you configure the server poll interval from integration settings (1-24 hours).
- Built with inspiration from [@xirixiz/homeassistant-afvalwijzer](https://github.com/xirixiz/homeassistant-afvalwijzer), but focused on **cleaning services** instead of **garbage collection**.

---

## 📦 Supported Providers
Currently, the integration supports the following providers/communities:

| Provider   |
|------------|
| **cleanprofs** |

> ⚠️ Availability depends on whether your municipality or service provider is supported and/or can be added.

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

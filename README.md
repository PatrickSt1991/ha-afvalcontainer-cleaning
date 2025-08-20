# 🧼 Afvalcontainer Cleaning

<img src="https://raw.githubusercontent.com/PatrickSt1991/ha-afvalcontainer-cleaning/refs/heads/main/clean-container.png" alt="clean container" width="400">

A **Home Assistant integration** for monitoring **garbage container cleaning schedules**.  

Need to know when your garbage containers will be cleaned?  
This integration adds **sensors** to Home Assistant that track cleaning services, so you’ll never miss a cleaning appointment again.  

---

## ✨ Features
- Adds `sensor.cleaningcontainer_*` entities in Home Assistant.  
- Tracks upcoming container cleaning schedules.  
- Supports multiple providers (see below).  
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

### HACS (recommended)
1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant.  
2. Go to **HACS → Integrations → Custom Repositories**.  
3. Add this repository URL and select **Integration**.  
4. Install the integration and restart Home Assistant.  

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
#!/usr/bin/env python3
"""
Sensor component for AfvalDienst
Author: Bram van Dartel - xirixiz

import afvalwijzer
from afvalwijzer.collector.mijnafvalwijzer import AfvalWijzer
AfvalWijzer().get_data('','','')

- Comment out __init__.py
- Update this file with your information (or the information you would like to test with, examples are in that file)
- Then run python3 -m afvalwijzer.tests.test_module from this path <some dir>/homeassistant-afvalwijzer/custom_components 

"""
from ..collector import cleanprofs

from ..collector.collector import MainCollector

# Common
suffix = ""
exclude_pickup_today = "True"
date_isoformat = "True"
default_label = "geen"
exclude_list = ""

# CleanProfs
provider = "cleanprofs"
postal_code = "1312ET"
street_number = "5"

# postal_code = postal_code.strip().upper()

collector = MainCollector(
    provider,
    postal_code,
    street_number,
    suffix,
    exclude_pickup_today,
    date_isoformat,
    exclude_list,
    default_label,
)

# MainCollector(
#     provider,
#     postal_code,
#     street_number,
#     suffix,
#     exclude_pickup_today,
#     exclude_list,
#     default_label,
# )

# data = XimmioCollector().get_waste_data_provider("meerlanden", postal_code2, street_number2, suffix, default_label, exclude_list)
# data2 = MijnAfvalWijzerCollector().get_waste_data_provider("mijnafvalwijzer", postal_code, street_number, suffix, default_label, exclude_list)


#########################################################################################################
print("\n")

print(f"Data collected from: {provider} with postcal code: {postal_code}")
print("\n")

print(collector.waste_data_with_today)
print(collector.waste_data_without_today)
print(collector.waste_data_custom)
print(collector.waste_types_provider)
print(collector.waste_types_custom)

print("\n")

# for key, value in afval1.items():
#     print(key, value)

# print("\n")

# for key, value in afval2.items():
#     print(key, value)
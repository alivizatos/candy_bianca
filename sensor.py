"""Sensor platform for candy_bianca integration."""
from __future__ import annotations

import logging
import json
import os
import requests
import binascii
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug(f"Setting up sensor platform with entry data: {entry.data}")

    device_type = entry.data["device_type"]

    sensors = []

    common_sensors = {
        "StatoWiFi": "Wifi Status",
        "CodiceErrore": "Error Code",
        "MetaCarico": "Half Load",
        "StartStop": "Start/Stop",
        "TreinUno": "3in1",
        "Eco": "Eco Mode",
        "Program": "Program",
        "ExtraDry": "Extra Dry",
        "OpenDoorOpt": "Open Door Option",
        "DelayStart": "Delay Start",
        "RemTime": "Remaining Time",
        "MissSalt": "Salt Missing",
        "MissRinse": "Rinse Missing",
        "OpenDoor": "Door Open",
        "Reset": "Reset",
        "CheckUp": "Checkup",
        }
    
    if device_type == "statusDWash":
      device_sensors = {
          "StatoDWash": "Dishwasher Status"
         }
    elif device_type == "statusLavatrice":
         device_sensors = {
          "StatoLavatrice": "Washing Machine Status"
         }

    sensors_mapping = {**common_sensors, **device_sensors}

    for sensor_type, sensor_name in sensors_mapping.items():
        sensors.append(CandyBiancaSensor(hass, entry, sensor_type, sensor_name, device_type))

    async_add_entities(sensors, update_before_add=True)


class CandyBiancaSensor(SensorEntity):
    """Representation of a Candy Bianca sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, sensor_type: str, sensor_name: str, device_type: str) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._attr_name = f"{entry.data['name']} {sensor_name}"
        self._ip_address = entry.data["ip_address"]
        self._encrypted = entry.data["encrypted"]
        self._key = entry.data["key"]
        self._attr_unique_id = f"{entry.entry_id}-{sensor_type}"
        self._sensor_type = sensor_type
        self._device_type = device_type
        self._state = None
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
            """Fetch new state data for the sensor."""
            _LOGGER.debug(f"Updating sensor data for {self._attr_name}")
            try:
                url = f"http://{self._ip_address}/http-read.json?encrypted={'1' if self._encrypted else '0'}"

                response = await self._hass.async_add_executor_job(
                    requests.get, url
                )
                response.raise_for_status()

                hex_data = response.text.strip()
                _LOGGER.debug(f"Hex data received: {hex_data}")

                 # XOR Decryption
                if self._encrypted and self._key:
                    try:
                         key = self._key
                         key_bytes = key.encode()

                         if len(hex_data) % 2 != 0:
                             _LOGGER.error(f"Odd length hex string before xor: {hex_data}")
                             self._state = "error"
                             self._attr_extra_state_attributes = {"error": "Odd length hex string before xor"}
                             return

                         data_bytes = binascii.unhexlify(hex_data)
                         decrypted_data_bytes = bytearray()


                         for i, byte in enumerate(data_bytes):
                             decrypted_data_bytes.append(byte ^ key_bytes[i % len(key_bytes)])

                         decrypted_data = decrypted_data_bytes.decode("utf-8", errors="ignore")

                         _LOGGER.debug(f"Decrypted data after XOR: {decrypted_data}")
                    except Exception as xor_err:
                         _LOGGER.error(f"XOR Decryption Error {xor_err}")
                         self._state = "error"
                         self._attr_extra_state_attributes = {"error": f"XOR decryption error: {xor_err}"}
                         return
                else:
                     decrypted_data = hex_data


                try:
                   json_data = json.loads(decrypted_data)
                   status_data = json_data.get(self._device_type, {})
                   self._state = status_data.get(self._sensor_type)

                   if self._sensor_type == "CodiceErrore" and self._state != "E0":
                       self._state = "Error"
                   if self._sensor_type == "StatoDWash":
                         states = {
                            "0": "IDLE",
                            "1": "PRE_WASH",
                            "2": "WASH",
                            "3": "RINSE",
                            "4": "DRYING",
                            "5": "FINISHED"
                            }
                         self._state = states.get(self._state, self._state)
                   if self._sensor_type == "StatoLavatrice":
                         states = {
                            "0": "IDLE",
                            "1": "PRE_WASH",
                            "2": "WASH",
                            "3": "RINSE",
                            "4": "SPIN",
                            "5": "FINISHED"
                            }
                         self._state = states.get(self._state, self._state)

                except json.JSONDecodeError:
                    self._state = "error"
                    self._attr_extra_state_attributes = {"error": "Invalid JSON response"}

            except requests.exceptions.RequestException as e:
                self._state = "error"
                _LOGGER.error(f"Error during request: {e}")
                self._attr_extra_state_attributes = {"error": f"Error during request: {e}"}
            except Exception as e:
                self._state = "error"
                _LOGGER.error(f"An unexpected error occurred: {e}")
                self._attr_extra_state_attributes = {"error": f"An unexpected error occurred: {e}"}


    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._state
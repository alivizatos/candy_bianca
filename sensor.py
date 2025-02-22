"""Sensor platform for candy_bianca integration."""

from __future__ import annotations

import logging
import json
import binascii

import requests
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.info(f"Setting up sensor platform with entry data: {entry.data}")

    coordinator: CandyBiancaCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"Coordinator retrieved from hass.data: {coordinator}")

    device_type = entry.data["device_type"]

    sensors = []

    if device_type == "statusDWash":
        sensors_mapping = {
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
            "StatoDWash": "Dishwasher Status",
        }

    elif device_type == "statusLavatrice":
        sensors_mapping = {
            "StatoLavatrice": "Washing Machine Status",
            "WiFiStatus": "Remote Control Status",
            "Err": "Error Code",
            "MachMd": "Machine Mode",
            "Pr": "Program",
            "PrPh": "Program Phase",
            "PrCode": "Program Code",
            "SLevel": "Soil Level",
            "Temp": "Temperature",
            "SpinSp": "Spin Speed",
            "Opt1": "Prewash Setting",
            "Opt2": "Hygiene Plus Setting",
            "Opt3": "Option 3",
            "Opt4": "Option 4",
            "Opt5": "Extra Rinse setting",
            "Opt6": "Option 6",
            "Opt7": "Option 7",
            "Opt8": "Option 8",
            "Opt9": "Option 9",
            "Steam": "Steam",
            "DryT": "Extra Dry",
            "DelVal": "Delay Start",
            "RemTime": "Remaining Time",
            "RecipeId": "Recipe ID",
            "Lang": "Language",
            "FillR": "Fill Percent",
            "DisTestOn": "Display Test On",
            "DisTestRes": "Display Test Result",
            "CheckUpState": "Checkup",
        }
    else:
        sensors_mapping = {}

    for sensor_type, sensor_name in sensors_mapping.items():
        sensors.append(
            CandyBiancaSensor(
                coordinator,
                hass,
                entry,
                sensor_type,
                sensor_name,
                device_type,
                sensors_mapping,
            )
        )

    async_add_entities(sensors)
    _LOGGER.info(f"Entities added: {sensors}")


class CandyBiancaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Candy Bianca sensor."""

    sensors_mapping = {}
    _attr_device_class = None

    def __init__(
        self,
        coordinator: CandyBiancaCoordinator,
        hass: HomeAssistant,
        entry: ConfigEntry,
        sensor_type: str,
        sensor_name: str,
        device_type: str,
        sensors_mapping: dict[str, str] = {},
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hass = hass
        self._attr_name = f"{entry.data['name']} {sensor_name}"
        self._attr_unique_id = f"{entry.entry_id}-{sensor_type}"
        self._sensor_type = sensor_type
        self._device_type = device_type
        self._state = None
        self._attr_extra_state_attributes = {}
        self._update_state()
        _LOGGER.info(
            f"Sensor initialized: {self._attr_name}, unique_id: {self._attr_unique_id}, sensor_type: {self._sensor_type}"
        )
        CandyBiancaSensor.sensors_mapping = sensors_mapping

        if self._sensor_type == "Program" or self._sensor_type == "Pr":
            self._attr_device_class = "program"

    async def async_set_program(self, program: str) -> None:
        """Set a new program to the appliance."""
        _LOGGER.debug(f"Setting new program to: {program} for {self._attr_name}")

        raw_program = await self._untranslate_program(program)
        if not raw_program:
            raise HomeAssistantError(f"Could not untranslate program value: {program}")

        encoded_data = await self._encode_data(raw_program)
        if not encoded_data:
            raise HomeAssistantError(f"Could not encode data: {raw_program}")

        try:
            url = f"http://{self.coordinator._ip_address}/http-write.json?encrypted=1&data={encoded_data}"
            _LOGGER.info(f"Sending url: {url}")

            response = await self._hass.async_add_executor_job(requests.get, url)
            response.raise_for_status()
            _LOGGER.info(f"Response status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error during request: {e}")
            raise HomeAssistantError(f"Error sending program: {e}")
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred: {e}")
            raise HomeAssistantError(f"An unexpected error occurred: {e}")

    async def _untranslate_program(self, program: str) -> str | None:
        """Untranslate the program value to its raw value."""
        _LOGGER.debug(f"Untranslating program: {program}")

        if self._device_type == "statusDWash":
            program_mapping = {
                "Intensive 75°C": "P2",
                "Normal 60°C": "P5",
                "Eco 45°C": "P8",
                "Zoom 60°C": "P19",
                "Pre-Wash": "P12",
            }
        elif self._device_type == "statusLavatrice":
            program_mapping = {
                "Intensive 75°C": "P2",
                "Normal 60°C": "P5",
                "Eco 45°C": "P8",
                "Zoom 60°C": "P19",
                "Pre-Wash": "P12",
            }
        else:
            program_mapping = {}

        raw_program = program_mapping.get(program)
        _LOGGER.debug(f"Raw program: {raw_program}")
        return raw_program

    async def _encode_data(self, data: str) -> str | None:
        """Encode the data using XOR encryption if enabled."""
        _LOGGER.info(f"Encoding data: {data}, encrypted: {self.coordinator._encrypted}")

        if not self.coordinator._encrypted:
            _LOGGER.info(f"Not encrypted")
            return data

        if not self.coordinator._key:
            _LOGGER.error(f"Key is empty")
            return None

        try:
            key_bytes = self.coordinator._key.encode()
            data_bytes = data.encode()
            encoded_data_bytes = bytearray()

            for i, byte in enumerate(data_bytes):
                encoded_data_bytes.append(byte ^ key_bytes[i % len(key_bytes)])

            encoded_data = binascii.hexlify(encoded_data_bytes).decode()
            _LOGGER.info(f"Encoded data: {encoded_data}")
            return encoded_data
        except Exception as e:
            _LOGGER.error(f"Encoding error: {e}")
            return None

    def _update_state(self) -> None:
        """Update the sensor state from the coordinator data."""
        if self.coordinator.json_data:
            status_data = self.coordinator.json_data.get(self._device_type, {})
            #            _LOGGER.debug(f"Raw JSON data for {self._device_type}: {status_data}")

            if self._device_type == "statusDWash":
                self._state = status_data.get(self._sensor_type)
                #                _LOGGER.debug(f"Sensor: {self._sensor_type}, Raw Value: {self._state}")  # Debug for translation

                if self._sensor_type == "StatoWiFi":
                    if self._state == "1":
                        self._state = "Remote Control"
                    elif self._state == "0":
                        self._state = "No Remote Control"
                    else:
                        self._state = "Unknown"
                if self._sensor_type == "CodiceErrore":
                    if self._state == "0" or self._state == "E0":
                        self._state = "Healthy"
                    elif self._state == "E2":
                        self._state = "No Water Input"
                    else:
                        self._state = "Error"
                if self._sensor_type == "StatoDWash":
                    states = {
                        "0": "IDLE",
                        "1": "PRE_WASH",
                        "2": "WASH",
                        "3": "RINSE",
                        "4": "DRYING",
                        "5": "FINISHED",
                    }
                    self._state = states.get(self._state, self._state)
                if self._sensor_type == "MissSalt":
                    if self._state == "0":
                        self._state = "Salt OK"
                    elif self._state == "1":
                        self._state = "Salt Missing"
                if self._sensor_type == "MissRinse":
                    if self._state == "0":
                        self._state = "Rinse OK"
                    elif self._state == "1":
                        self._state = "Rinse Missing"
                if self._sensor_type == "TreinUno":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                if self._sensor_type == "Eco":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                if self._sensor_type == "ExtraDry":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                if self._sensor_type == "OpenDoor":
                    if self._state == "0":
                        self._state = "Closed"
                    elif self._state == "1":
                        self._state = "Open"
                if self._sensor_type == "MetaCarico":
                    if self._state == "0":
                        self._state = "Full Load"
                    elif self._state == "1":
                        self._state = "Half Load"
                if self._sensor_type == "Program":
                    if self._state == "P19":
                        self._state = "Zoom 39mins 60°C"
                    elif self._state == "P2":
                        self._state = "P1 75°C"
                    elif self._state == "P5":
                        self._state = "Universal 60°C"
                    elif self._state == "P8":
                        self._state = "ECO 45°C"
                    elif self._state == "P12":
                        self._state = "PreWash 5mins"
                if self._sensor_type == "RemTime":
                    try:
                        minutes = int(self._state)
                        hours = minutes // 60
                        minutes_rem = minutes % 60
                        self._state = f"{hours} hours {minutes_rem} minutes"
                    except (ValueError, TypeError):
                        _LOGGER.error(f"Error converting RemTime value: {self._state}")
                        self._state = "Error"

            # Update state for statusLavatrice
            elif self._device_type == "statusLavatrice":
                self._state = status_data.get(self._sensor_type)
                _LOGGER.debug(
                    f"Sensor: {self._sensor_type}, Raw Value: {self._state}"
                )  # Debug for translation

                if self._sensor_type == "WiFiStatus":
                    if self._state == "0":
                        self._state = "No Remote Control"
                    elif self._state == "1":
                        self._state = "Remote Control"
                    else:
                        self._state = "Unknown"
                if self._sensor_type == "Err":
                    if self._state == "0":
                        self._state = "No errors"
                    else:
                        self._state = "Error"
                if self._sensor_type == "MachMd":
                    states = {
                        "1": "Idle",
                        "2": "Running",
                        "3": "Paused",
                        "4": "Delayed Start Selection",
                        "5": "Delayed Start Programmed",
                        "6": "Error",
                        "7": "Finished1",
                        "8": "Finished2",
                    }
                    self._state = states.get(self._state, self._state)
                if self._sensor_type == "PrPh":
                    states = {
                        "0": "Stopped",
                        "1": "Prewash",
                        "2": "Wash",
                        "3": "Rinse",
                        "4": "Last Rinse",
                        "5": "End",
                        "6": "Drying",
                        "7": "Error",
                        "8": "Steam",
                        "9": "Good Night",
                        "10": "Spin",
                    }
                    self._state = states.get(self._state, self._state)
                if self._sensor_type == "SLevel":
                    self._state = self._state
                if self._sensor_type == "Temp":
                    self._state = self._state + "°C"

                if self._sensor_type == "SpinSp":
                    self._state = str(int(self._state) * 100) + " RPM"

            if (
                self._sensor_type not in self.sensors_mapping
            ):  # Log for not mapped sensor_types
                _LOGGER.warning(
                    f"Sensor type '{self._sensor_type}' not mapped in _update_state for device_type '{self._device_type}'. Please check sensor_mapping."
                )

            if self._state is None:  # Log if state is None
                _LOGGER.warning(
                    f"Sensor state is None for sensor_type '{self._sensor_type}'. Raw state data: {status_data.get(self._sensor_type)}"
                )

        else:
            self._state = "error"
            self._attr_extra_state_attributes = {"error": "Data not available"}
            _LOGGER.debug(
                f"Sensor state error: {self._attr_name}, state: {self._state}"
            )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self) -> str | None:
        """Return the device class of the sensor."""
        return self._attr_device_class

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        # _LOGGER.debug(f"Listener added to coordinator: {self._attr_name}")

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # _LOGGER.debug(f"Coordinator update received: {self._attr_name}")
        self._update_state()
        self.async_write_ha_state()

"""Sensor platform for candy_bianca integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CandyBiancaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug(f"Setting up sensor platform with entry data: {entry.data}")

    coordinator: CandyBiancaCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(f"Coordinator retrieved from hass.data: {coordinator}")

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
        device_sensors = {"StatoDWash": "Dishwasher Status"}
    elif device_type == "statusLavatrice":
        device_sensors = {"StatoLavatrice": "Washing Machine Status"}
    else:
        device_sensors = {}  # Handle the case when device_type is neither "statusDWash" nor "statusLavatrice"

    sensors_mapping = {**common_sensors, **device_sensors}

    for sensor_type, sensor_name in sensors_mapping.items():
        sensors.append(
            CandyBiancaSensor(
                coordinator, hass, entry, sensor_type, sensor_name, device_type
            )
        )

    async_add_entities(sensors)
    _LOGGER.debug(f"Entities added: {sensors}")


class CandyBiancaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Candy Bianca sensor."""

    def __init__(
        self,
        coordinator: CandyBiancaCoordinator,
        hass: HomeAssistant,
        entry: ConfigEntry,
        sensor_type: str,
        sensor_name: str,
        device_type: str,
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
        _LOGGER.debug(f"Sensor initialized: {self._attr_name}, unique_id: {self._attr_unique_id}, sensor_type: {self._sensor_type}")

    def _update_state(self) -> None:
            """Update the sensor state from the coordinator data."""
            _LOGGER.debug(f"Updating state for: {self._attr_name}, sensor_type: {self._sensor_type}")
            if self.coordinator.json_data:
                status_data = self.coordinator.json_data.get(self._device_type, {})
                _LOGGER.debug(f"Status data: {status_data}")
                self._state = status_data.get(self._sensor_type)
                _LOGGER.debug(f"Raw state: {self._state}")

                if self._sensor_type == "StatoWiFi":
                    if self._state == "1":
                        self._state = "Remote Control"
                    elif self._state == "0":
                         self._state = "No Remote Control"
                    else:
                        self._state = "Unknown"
                    _LOGGER.debug(f"Translated StatoWiFi state: {self._state}")
                if self._sensor_type == "CodiceErrore":
                    if self._state == "E0":
                        self._state = "Healthy"
                    else:
                        _LOGGER.debug(f"Error code: {self._state}")
                        
                    _LOGGER.debug(f"Translated error code state: {self._state}")
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
                    _LOGGER.debug(f"Translated StatoDWash state: {self._state}")
                if self._sensor_type == "StatoLavatrice":
                    states = {
                        "0": "IDLE",
                        "1": "PRE_WASH",
                        "2": "WASH",
                        "3": "RINSE",
                        "4": "SPIN",
                        "5": "FINISHED",
                    }
                    self._state = states.get(self._state, self._state)
                    _LOGGER.debug(f"Translated StatoLavatrice state: {self._state}")
                if self._sensor_type == "MissSalt":
                    if self._state == "0":
                        self._state = "Salt OK"
                    elif self._state == "1":
                        self._state = "Salt Missing"
                    _LOGGER.debug(f"Translated MissSalt state: {self._state}")
                if self._sensor_type == "MissRinse":
                    if self._state == "0":
                        self._state = "Rinse OK"
                    elif self._state == "1":
                         self._state = "Rinse Missing"
                    _LOGGER.debug(f"Translated MissRinse state: {self._state}")
                if self._sensor_type == "TreinUno":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                    _LOGGER.debug(f"Translated TreinUno state: {self._state}")
                if self._sensor_type == "Eco":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                    _LOGGER.debug(f"Translated Eco state: {self._state}")
                if self._sensor_type == "ExtraDry":
                    if self._state == "0":
                        self._state = "Disabled"
                    elif self._state == "1":
                        self._state = "Enabled"
                    _LOGGER.debug(f"Translated ExtraDry state: {self._state}")
                if self._sensor_type == "OpenDoor":
                     if self._state == "0":
                        self._state = "Closed"
                     elif self._state == "1":
                        self._state = "Open"
                     _LOGGER.debug(f"Translated OpenDoor state: {self._state}")
                if self._sensor_type == "MetaCarico":
                    if self._state == "0":
                        self._state = "Full Load"
                    elif self._state == "1":
                        self._state = "Half Load"
                    _LOGGER.debug(f"Translated MetaCarico state: {self._state}")
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
                    _LOGGER.debug(f"Translated Program state: {self._state}")
                if self._sensor_type == "RemTime":
                    try:
                        minutes = int(self._state)
                        hours = minutes // 60
                        minutes = minutes % 60
                        self._state = f"{hours} hours {minutes} minutes"
                    except (ValueError, TypeError):
                         _LOGGER.error(f"Error converting RemTime value: {self._state}")
                         self._state = "Error"
                    _LOGGER.debug(f"Translated RemTime state: {self._state}")
                else:
                   _LOGGER.debug(f"No translation needed for sensor: {self._sensor_type}")
            else:
                 self._state = "error"
                 self._attr_extra_state_attributes = {"error": "Data not available"}
                 _LOGGER.debug(f"Sensor state error: {self._attr_name}, state: {self._state}")


    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._state
    
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
        _LOGGER.debug(f"Listener added to coordinator: {self._attr_name}")


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Coordinator update received: {self._attr_name}")
        self._update_state()
        self.async_write_ha_state()

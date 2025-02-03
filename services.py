"""Services for the candy_bianca integration."""

from __future__ import annotations

import logging
import json
import binascii
import requests

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the integration."""

    async def async_send_program(service: ServiceCall) -> None:
        """Send a new program to the appliance."""
        _LOGGER.debug(f"Service call data: {service.data}")

        device_name = service.data.get("device_name")  # Changed to device_name
        program = service.data.get("program")

        if not device_name:  # Changed to device_name
            raise HomeAssistantError(
                "device_name is required"
            )  # Changed to device_name
        if not program:
            raise HomeAssistantError("program is required")

        coordinator = None
        for coord in hass.data[DOMAIN].values():
            if (
                coord._entry.data["name"] == device_name
            ):  # Find coordinator by device_name
                coordinator = coord
                break

        if not coordinator:
            raise HomeAssistantError(
                f"Could not find device with name: {device_name}"
            )  # Error message updated

        ip_address = coordinator._ip_address
        encrypted = coordinator._encrypted
        key = coordinator._key
        device_type = coordinator._device_type

        _LOGGER.debug(
            f"Coordinator data: IP Address: {ip_address}, Encrypted: {encrypted}, Key: {key}, Device Type: {device_type}"
        )

        raw_program = await _untranslate_program(program, device_type, coordinator)
        if not raw_program:
            raise HomeAssistantError(f"Could not untranslate program value: {program}")

        encoded_data = await _encode_data(raw_program, encrypted, key)
        if not encoded_data:
            raise HomeAssistantError(f"Could not encode data: {raw_program}")

        try:
            url = f"http://{ip_address}/http-write.json?encrypted=1&data={encoded_data}"
            _LOGGER.debug(f"Sending url: {url}")

            response = await hass.async_add_executor_job(requests.get, url)
            response.raise_for_status()
            _LOGGER.debug(f"Response status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error during request: {e}")
            raise HomeAssistantError(f"Error during request: {e}")
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred: {e}")
            raise HomeAssistantError(f"An unexpected error occurred: {e}")

    async def async_set_program(service: ServiceCall) -> None:
        """Set a new program to the appliance."""
        _LOGGER.debug(f"Calling async_set_program: {service.data}")

        device_name = service.data.get("device_name")  # Changed to device_name
        program = service.data.get("program")

        if not device_name:  # Changed to device_name
            raise HomeAssistantError(
                "device_name is required"
            )  # Changed to device_name
        if not program:
            raise HomeAssistantError("program is required")

        # Attempt to find the program sensor by iterating through all entities
        program_entity_id = None
        program_state = None
        for entity_id in hass.states.async_entity_ids():
            state = hass.states.get(entity_id)
            if state and state.entity_id.startswith("sensor."):
                entity_device_name = state.name.rsplit(" ", 1)[0]
                if (
                    entity_device_name == device_name
                    and state.attributes.get("device_class") == "program"
                ):
                    program_entity_id = entity_id
                    program_state = state
                    break

        if not program_entity_id:
            _LOGGER.error(
                f"Could not find program entity with device name {device_name}. Available entities: {[entity_id for entity_id in hass.states.async_entity_ids()]}"
            )
            raise HomeAssistantError(
                f"Could not find program entity with device name {device_name}"
            )

        if program_state:
            # Extract the program from the entity's state.
            program_value = program_state.state
            _LOGGER.debug(f"Extracted program value: {program_value}")
            # Call send_program with the extracted program value
            await hass.services.async_call(
                DOMAIN,
                "send_program",
                {
                    "device_name": device_name,
                    "program": program_value,
                },
            )
        else:
            _LOGGER.error(f"Could not get the state of {program_entity_id}")
            raise HomeAssistantError(f"Could not get the state of {program_entity_id}")

    hass.services.async_register(
        DOMAIN,
        "set_program",
        async_set_program,
    )
    _LOGGER.debug(f"Service set_program registered")

    hass.services.async_register(
        DOMAIN,
        "send_program",
        async_send_program,
    )
    _LOGGER.debug(f"Service send_program registered")

    async def _untranslate_program(
        program: str, device_type: str, coordinator
    ) -> str | None:
        """Untranslate the program value to its raw value."""
        _LOGGER.debug(f"Untranslating program: {program}")

        if device_type == "statusDWash":
            program_mapping = {
                "Zoom 39mins 60°C": "P19",
                "P1 75°C": "P2",
                "Universal 60°C": "P5",
                "ECO 45°C": "P8",
                "PreWash 5mins": "P12",
            }
        elif device_type == "statusLavatrice":
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

    async def _encode_data(data: str, encrypted: bool, key: str) -> str | None:
        """Encode the data using XOR encryption if enabled."""
        _LOGGER.debug(f"Encoding data: {data}, encrypted: {encrypted}")

        if not encrypted:
            _LOGGER.debug(f"Not encrypted")
            return data

        if not key:
            _LOGGER.error(f"Key is empty")
            return None

        try:
            key_bytes = key.encode()
            data_bytes = data.encode()
            encoded_data_bytes = bytearray()

            for i, byte in enumerate(data_bytes):
                encoded_data_bytes.append(byte ^ key_bytes[i % len(key_bytes)])

            encoded_data = binascii.hexlify(encoded_data_bytes).decode()
            _LOGGER.debug(f"Encoded data: {encoded_data}")
            return encoded_data
        except Exception as e:
            _LOGGER.error(f"Encoding error: {e}")
            return None

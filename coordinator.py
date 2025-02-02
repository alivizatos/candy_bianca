"""Coordinator for candy_bianca integration."""

from __future__ import annotations

import logging
import json
import binascii
from datetime import timedelta


import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady


_LOGGER = logging.getLogger(__name__)


class CandyBiancaCoordinator(DataUpdateCoordinator):
    """Coordinator for candy_bianca integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._entry = entry
        self._ip_address = entry.data["ip_address"]
        self._encrypted = entry.data["encrypted"]
        self._key = entry.data["key"]
        self._device_type = entry.data["device_type"]
        self.json_data = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"Candy Bianca {entry.data['name']}",
            update_interval=timedelta(seconds=30),
        )
        _LOGGER.info(
            f"Coordinator initialized: {self.name}, update_interval: {self.update_interval}"
        )

    async def _async_update_data(self):
        """Fetch data from the api."""
        _LOGGER.debug(f"Fetching data for {self._entry.data['name']}")
        try:
            url = f"http://{self._ip_address}/http-read.json?encrypted={'1' if self._encrypted else '0'}"

            response = await self.hass.async_add_executor_job(requests.get, url)
            response.raise_for_status()

            hex_data = response.text.strip()

            # XOR Decryption
            if self._encrypted and self._key:
                try:
                    key = self._key
                    key_bytes = key.encode()

                    if len(hex_data) % 2 != 0:
                        _LOGGER.error(f"Odd length hex string before xor: {hex_data}")
                        return None

                    data_bytes = binascii.unhexlify(hex_data)
                    decrypted_data_bytes = bytearray()

                    for i, byte in enumerate(data_bytes):
                        decrypted_data_bytes.append(
                            byte ^ key_bytes[i % len(key_bytes)]
                        )

                    decrypted_data = decrypted_data_bytes.decode(
                        "utf-8", errors="ignore"
                    )
                except Exception as xor_err:
                    _LOGGER.error(f"XOR Decryption Error {xor_err}")
                    return None
            else:
                decrypted_data = hex_data

            try:
                self.json_data = json.loads(decrypted_data)
                return self.json_data
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON response")
                return None

        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error during request: {e}")
            return None
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred: {e}")
            return None

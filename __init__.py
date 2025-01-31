"""The candy_bianca integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta


from .const import DOMAIN, PLATFORMS
from .coordinator import CandyBiancaCoordinator


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up candy_bianca from a config entry."""

    _LOGGER.debug(f"Setting up integration with entry: {entry.data}")

    coordinator = CandyBiancaCoordinator(hass, entry)

    _LOGGER.debug(f"Coordinator created: {coordinator}")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug(
        f"Coordinator first refresh completed: {coordinator.last_update_success}"
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    _LOGGER.debug(
        f"Coordinator stored in hass.data: {hass.data[DOMAIN][entry.entry_id]}"
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug(f"Forwarded entry setups: {PLATFORMS}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading integration with entry: {entry.data}")

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

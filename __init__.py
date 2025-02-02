"""The candy_bianca integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta


from .const import DOMAIN, PLATFORMS
from .coordinator import CandyBiancaCoordinator
from .services import async_setup_services


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up candy_bianca from a config entry."""

    _LOGGER.info(f"Setting up integration with entry: {entry.data}")

    coordinator = CandyBiancaCoordinator(hass, entry)

    _LOGGER.info(f"Coordinator created: {coordinator}")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.info(
        f"Coordinator first refresh completed: {coordinator.last_update_success}"
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    _LOGGER.info(
        f"Coordinator stored in hass.data: {hass.data[DOMAIN][entry.entry_id]}"
    )
    _LOGGER.info(f"Setting up entry")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info(f"Forwarded entry setups: {PLATFORMS}")
    await async_setup_services(hass)
    _LOGGER.info(f"Setup entry complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"Unloading integration with entry: {entry.data}")

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

"""Config flow for candy_bianca integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for candy_bianca."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                return self.async_create_entry(title=user_input["name"], data=user_input)
            except Exception as e:
                 _LOGGER.error(f"Error during config flow: {e}")
                 errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("ip_address"): str,
                    vol.Required("device_type", default="statusDWash"): vol.In(
                        {
                            "statusDWash": "Dishwasher",
                            "statusLavatrice": "Washing Machine",
                        }
                    ),
                    vol.Optional("encrypted", default=False): bool,
                    vol.Optional("key", default=""): str,
                }
            ),
            errors=errors,
        )
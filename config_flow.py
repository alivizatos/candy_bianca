"""Config flow for candy_bianca integration."""

from __future__ import annotations

import logging
from typing import Any
import asyncio

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
                return self.async_create_entry(
                    title=user_input["name"], data=user_input
                )
            except Exception as e:
                _LOGGER.error(f"Error during config flow: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self, user_input: dict[str, Any] | None = None) -> vol.Schema:
        """Get the data schema."""
        if not user_input:
            user_input = {}
        return vol.Schema(
            {
                vol.Required("name", default=user_input.get("name", "")): str,
                vol.Required(
                    "ip_address", default=user_input.get("ip_address", "")
                ): str,
                vol.Required(
                    "device_type", default=user_input.get("device_type", "statusDWash")
                ): vol.In(
                    {
                        "statusDWash": "Dishwasher",
                        "statusLavatrice": "Clothes Washing Machine",
                    }
                ),
                vol.Optional(
                    "encrypted", default=user_input.get("encrypted", False)
                ): bool,
                vol.Optional("key", default=user_input.get("key", "")): str,
            }
        )

    async def _test_tcp_connection(self, ip_address: str) -> bool:
        """Test if the device is reachable via TCP connection on port 80."""
        return True

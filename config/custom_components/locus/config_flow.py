"""Config flow for Locus Diagnostics integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class LocusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Locus Diagnostics."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step via the user interface."""
        if user_input is not None:
            # Validate the input here
            return self.async_create_entry(title="My Device", data=user_input)

        # Show a form with a simple text field
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("host"): str})
        )

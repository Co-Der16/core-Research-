"""Config flow for Locus Diagnostics integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class LocusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Locus Diagnostics."""

    VERSION = 1

    @override
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the initial step via the user interface."""
        if user_input is not None:
            return self.async_create_entry(
                title={user_input["username"]}, data=user_input
            )
        data_schema = {
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("ssl_options"): section(
                vol.Schema(
                    {
                        vol.Required("ssl", default=True): bool,
                        vol.Required("verify_ssl", default=True): bool,
                    }
                ),
                {"collapsed": False},
            ),
        }

        if self.show_advanced_options:
            data_schema[vol.Optional("allow_groups")] = selector(
                {
                    "select": {
                        "options": ["vacuum", "thermostat", "light"],
                    }
                }
            )
        # Show a form with a simple text field
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))

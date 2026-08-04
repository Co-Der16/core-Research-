"""Idk what to do here if I'm being honest."""

import logging

from homeassistant.config_entries import ConfigEntry as ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

DOMAIN = "locus"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Locus component from YAML (legacy support)."""
    _logger.debug("Locus component successfully registered in the backend.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Locus component from a UI configuration entry."""
    # This prepares Home Assistant's memory space for your custom entities
    hass.data.setdefault(DOMAIN, {})

    async def monitor_matter_stream(hass: HomeAssistant):
        """Listens natively to the internal event bus with zero network sockets."""

        async def handle_matter_event(event):
            """This runs instantly whenever the Matter integration logs a state or error."""
            event_data = event.data
            if "error_code" in str(event_data) or "CHIP_ERROR" in str(event_data):
                _logger.critical("🚨 Caught error internally: %s", event_data)

        # Listen directly to the core application event memory layer
        hass.bus.async_listen("matter_event", handle_matter_event)

    return True


# Update these variables with your local setup details
HA_URL = "ws://homeassistant.local:8123/api/websocket"
LONG_LIVED_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIyZWYxZmIxOWI2YmU0M2M4OWRkNzFiMjFiM2I3MzNmOSIsImlhdCI6MTc4NTQxOTU5MCwiZXhwIjoyMTAwNzc5NTkwfQ.DfvQZTzwzrm0mSY4D2nvSktaJiOYHjs1Op_3KmJT2UQ"

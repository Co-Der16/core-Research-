"""The Locus integration is a custom component for Home Assistant that monitors the internal event bus for state changes and logs them, particularly focusing on entities related to the Matter integration. It provides a configuration flow for setting up the integration through the Home Assistant UI, allowing users to input their credentials and configure SSL options. The integration also supports legacy YAML configuration."""

import logging

from homeassistant.config_entries import ConfigEntry as ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType

DOMAIN = "locus"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Locus component from YAML (legacy support)."""
    _logger.debug(
        "Locus component successfully registered in the backend. writing extra to test if it works"
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the component from a UI configuration entry."""
    # This prepares Home Assistant's memory space for your custom entities
    hass.data.setdefault(DOMAIN, {})
    _logger.info("test 2 to see if it prints to log")

    @callback
    def monitor_matter_stream(event: Event):
        """Queries the internal event bus for state changes and logs them."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        _logger.log(logging.INFO, "some state thing happened: %s", event.data)

        if not new_state:
            return

        ent_reg = er.async_get(hass)
        entity_entry = ent_reg.async_get(entity_id)
        device_id = entity_entry.device_id if entity_entry else "No Device ID Found"

        if entity_entry and entity_entry.platform == "matter":
            _logger.info(
                "🚨 [MATTER] Caught state change for entity '%s' (device_id: %s): %s",
                entity_id,
                device_id,
                new_state.state,
            )
        elif not entity_entry:
            _logger.info(
                "🌍 [SYSTEM] Caught global entity change '%s': %s",
                entity_id,
                new_state.state,
            )

    target_entities = hass.states.async_entity_ids(
        "light"
    ) + hass.states.async_entity_ids("switch")
    async_track_state_change_event(hass, target_entities, monitor_matter_stream)

    return True

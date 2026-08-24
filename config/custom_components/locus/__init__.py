"""The Locus integration is a custom component for Home Assistant that monitors the internal event bus for state changes and logs them, particularly focusing on entities related to the Matter integration. It provides a configuration flow for setting up the integration through the Home Assistant UI, allowing users to input their credentials and configure SSL options. The integration also supports legacy YAML configuration."""

import logging

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry as ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType

DOMAIN = "locus"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_logger = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER]


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
        device_id = (
            entity_entry.unique_id
            if entity_entry
            else entity_entry.device_id
            if entity_entry
            else "unknown"
        )

        _logger.info(
            "State change in '%s' (device_id: %s): is now %s",
            entity_id,
            device_id,
            new_state.state,
        )

        def auto_dock(
            doAutoDocking: bool = entry.data["user_input"]["vacuum_options"][
                "auto_dock"
            ],
            batteryPercent: int = new_state.attributes.get("battery"),
            entity_id: str = entity_id,
        ):
            """Auto-docks a vacuum if under a certain battery percentage."""

            if not doAutoDocking:
                return
            if (
                batteryPercent
                <= entry.data["user_input"]["vacuum_options"]["auto_dock percent"]
            ):
                persistent_notification.create(
                    hass,
                    message=f"Battery at auto-dock threshold for vacuum {entity_id} \n Docking!",
                    title="Low Battery",
                    notification_id=f"locus_low_battery{entity_id}",
                )
                hass.async_create_task(
                    hass.services.async_call(
                        "vacuum",
                        "return_to_base",
                        {"entity_id": entity_id},
                    )
                )
            return

        auto_dock()
        if new_state.state == "error":
            _logger.error(
                "Error state detected for '%s' (device_id: %s, error = %s) %s, fix is %s, id is %s",
                entity_id,
                device_id,
                new_state.attributes.get("fault_reason", "No fault reason provided"),
                new_state.attributes.get("fault_text", "No fault text provided"),
                new_state.attributes.get("fault_fix", "No fix provided"),
                new_state.attributes.get("fault_id", "No fault ID provided"),
            )
            persistent_notification.create(
                hass,
                message=f"Device ID: {device_id}\nError: {new_state.attributes.get('fault_reason', 'No fault reason provided')}\nDetails: {new_state.attributes.get('fault_text', 'No fault text provided')}\nFix: {new_state.attributes.get('fault_fix', 'No fix provided')}\nFault ID: {new_state.attributes.get('fault_id', 'No fault ID provided')}",
                title=f"Error detected in {entity_id}",
                notification_id=f"locus_error_{entity_id}",
            )

    target_entities = hass.states.async_entity_ids("vacuum")
    async_track_state_change_event(hass, target_entities, monitor_matter_stream)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

"""The Locus integration is a custom component for Home Assistant that monitors the internal event bus for state changes and logs them, particularly focusing on entities related to the Matter integration. It provides a configuration flow for setting up the integration through the Home Assistant UI, allowing users to input their credentials and configure SSL options. The integration also supports legacy YAML configuration."""

import json
import logging
from pathlib import Path

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry as ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    Event,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    callback,
)
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType

from .matter_errors import matter_error_to_locus_code

DOMAIN = "locus"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_logger = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


def get_locus_error_from_matter(
    matter_error: str,
    db: list[dict],
) -> dict | None:
    """Convert a Matter error into its Locus database entry."""
    locus_code = matter_error_to_locus_code(matter_error)

    if locus_code is None:
        return None

    for error in db:
        if error["error_code"] == locus_code:
            return error

    return None


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

    @callback
    def error_notifier(event: Event):
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

        # auto_dock()
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
    async_track_state_change_event(hass, target_entities, error_notifier)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    locus_error_db = Path(__file__).parent
    db_path = Path(locus_error_db) / "errors_db.json"

    def load_db():
        with Path.open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    database_data = await hass.async_add_executor_job(load_db)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"database": database_data}

    _logger.info(
        "Locus error database loaded successfully with %d entries.",
        len(database_data),
    )

    async def async_search_errors(call: ServiceCall) -> ServiceResponse:
        """Searches Locus database for errors. Mainly AI made."""
        search_query = call.data.get("query", "").lower()
        device_filter = call.data.get("device_type", "").lower()

        domain_data = hass.data.get(DOMAIN, {})
        entry_data = domain_data.get(entry.entry_id, {})
        db = entry_data.get("database")

        _logger.info(
            "Locus error database loaded successfully with %d entries. Searching with query %s",
            len(db),
            search_query,
        )

        results = []

        for error in db:
            # If a device filter is set, skip errors that don't match
            # device type.
            if device_filter and error["device_type"] != device_filter:
                continue

            # Match text against error_code, summary, or description.
            if (
                search_query in error["error_code"].lower()
                or search_query in error["summary"].lower()
                or search_query in error["description"].lower()
            ):
                results.append(error)

        _logger.info(
            "Search completed. Found %d matching errors for query '%s' "
            "with device filter '%s'.",
            len(results),
            search_query,
            device_filter,
        )

        persistent_notification.create(
            hass,
            message=(
                f"Search completed. Found {len(results)} matching errors "
                f"for query '{search_query}' with device filter "
                f"'{device_filter}'."
            ),
            title="Locus Error Search Results",
            notification_id=f"locus_search_results_{entry.entry_id}",
        )

        return {"errors": results}

    hass.services.async_register(
        DOMAIN,
        "search_errors",
        async_search_errors,
        supports_response=True,
    )

    return True

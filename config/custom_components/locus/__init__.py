"""The Locus integration is a custom component for Home Assistant that monitors the internal event bus for state changes and logs them, particularly focusing on entities related to the Matter integration.

It provides a configuration flow for setting up the integration through the Home Assistant UI, allowing users to input their credentials and configure SSL options. The integration also supports legacy YAML configuration.
"""

import json
import logging
from pathlib import Path

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    EVENT_STATE_CHANGED,
    Event,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    callback,
)
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
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
    """Set up the Locus component."""
    db_path = Path(__file__).parent / "errors_db.json"

    def load_db():
        with Path.open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    database_data = await hass.async_add_executor_job(load_db)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["database"] = database_data

    _logger.info(
        "Locus error database loaded successfully with %d entries.",
        len(database_data),
    )

    async def async_search_errors(call: ServiceCall) -> ServiceResponse:
        """Search Locus database for errors."""
        search_query = call.data.get("query", "").lower()
        device_filter = call.data.get("device_type", "").lower()

        status_filters = {}

        for status_name in (
            "wifi_status",
            "hass_status",
            "phys_status",
            "battery_status",
        ):
            requested_status = call.data.get(status_name)

            if requested_status == "true":
                requested_status = True
            elif requested_status == "false":
                requested_status = False

            status_filters[status_name] = requested_status

        db = hass.data[DOMAIN]["database"]

        results = []

        for error in db:
            if device_filter and error["device_type"] != device_filter:
                continue

            if search_query and not (
                search_query in error["error_code"].lower()
                or search_query in error["summary"].lower()
                or search_query in error["description"].lower()
            ):
                continue

            statuses = error.get("statuses", {})
            status_mismatch = False

            for status_name, requested_status in status_filters.items():
                if requested_status is not None:
                    allowed_statuses = statuses.get(status_name, [])

                    if requested_status not in allowed_statuses:
                        status_mismatch = True
                        break

            if status_mismatch:
                continue

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
            notification_id="locus_search_results",
        )

        return {"errors": results}

    hass.services.async_register(
        DOMAIN,
        "search_errors",
        async_search_errors,
        supports_response=True,
    )

    @callback
    def state_listener(event: Event):
        """Handle state changes relevant to Locus."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        if not entity_id or not new_state:
            return

        ent_reg = er.async_get(hass)
        entity_entry = ent_reg.async_get(entity_id)

        unique_id = ""
        if entity_entry and entity_entry.unique_id:
            unique_id = entity_entry.unique_id

        #
        # PART 1: Normal vacuum errors
        #
        if entity_id.startswith("vacuum.") and new_state.state == "error":
            _logger.info(
                "Locus detected vacuum error state: %s",
                entity_id,
            )

            persistent_notification.create(
                hass,
                message=f"Vacuum {entity_id} entered error state.",
                title="Locus Vacuum Error",
                notification_id=f"locus_vacuum_{entity_id}",
            )

            _logger.error(
                "Vacuum error detected: %s",
                entity_id,
            )

        #
        # PART 2: Matter robot vacuum operational errors
        #
        if "RvcOperationalStateOperationalError" not in unique_id:
            return

        matter_error = new_state.state

        _logger.info(
            "Matter error sensor updated: %s -> %s",
            entity_id,
            matter_error,
        )

        if matter_error in ("no_error", "unknown"):
            return

        db = hass.data[DOMAIN]["database"]

        locus_error = get_locus_error_from_matter(
            matter_error,
            db,
        )

        if not locus_error:
            _logger.warning(
                "No Locus entry found for Matter error: %s",
                matter_error,
            )
            return

        _logger.error(
            "Mapped Matter error %s -> %s",
            matter_error,
            locus_error["error_code"],
        )

        persistent_notification.create(
            hass,
            message=(
                f"Error: {locus_error['summary']}\n\n"
                f"Details: {locus_error['description']}\n\n"
                f"Fixes:\n"
                f"{chr(10).join(locus_error['recommended_fixes'])}"
            ),
            title=f"Locus: {locus_error['summary']}",
            notification_id=f"locus_matter_{entity_id}",
        )

    hass.bus.async_listen(
        EVENT_STATE_CHANGED,
        state_listener,
    )

    _logger.info("Locus state listener registered.")

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up the component from a UI configuration entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True

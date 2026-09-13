"""Locus integration config flow."""

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN

# Compute the errors directory relative to this integration package. This
# ensures the config flow works regardless of how Home Assistant's working
# directory is configured.
TARGET_DIR = Path(__file__).parent / "errors"
_logger = logging.getLogger(__name__)


def load_directory_contents(directory_path: str) -> list[dict[str, str]]:
    """Synchronous file/folder retrieval to be run in an executor thread.

    Returns a list of selector option dicts with `value` and `label` keys.
    """
    base = Path(directory_path)
    if not base.exists():
        return []

    options: list[dict[str, str]] = []
    for item in sorted(base.iterdir()):
        if item.name.startswith("."):
            continue
        # Use relative path from the errors directory as the value so nested
        # files/folders can be referenced later.
        rel = str(item.relative_to(base))
        options.append({"value": rel, "label": item.name})

    return options


class DirectoryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for loading dynamic directory-based error fixes."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # 2. Show a simple confirmation button if user_input is empty
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {}
                ),  # Empty schema = no text fields, just a "Submit" prompt
            )
        return self.async_create_entry(
            title="Locus Errors Database",
            data={},  # Keep this empty since your database file is packaged locally
        )

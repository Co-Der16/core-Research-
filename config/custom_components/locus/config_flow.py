"""Locus integration config flow."""

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

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

        if user_input is not None:
            if "user_input" not in self.context:
                self.context["user_input"] = {}

            self.context["user_input"].update(user_input)
            if user_input.get("vacuum"):
                return await self.async_step_vacuum_options()
            return self.async_create_entry(
                title=f"Locus ({user_input.get('vacuum')})",
                data=user_input,
            )

        # Build the form schema using the selector helper; selector expects
        # a list of option dicts with `value`/`label` keys.
        data_schema = vol.Schema(
            {
                vol.Optional("friendly_name", default="Locus"): str,
                vol.Optional("vacuum", default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_vacuum_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Options for if the user selects that they are using Locus with a vacuum."""
        if user_input is not None:
            self.context["user_input"]["vacuum_options"] = user_input
            return self.async_create_entry(title="Locus", data=self.context)
        data_schema_vacuum = vol.Schema(
            {
                vol.Optional("auto_dock"): bool,
                vol.Optional("auto_dock percent"): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=100, step=1, mode=NumberSelectorMode.SLIDER
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="vacuum_options", data_schema=data_schema_vacuum
        )

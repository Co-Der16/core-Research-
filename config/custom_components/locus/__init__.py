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
    return True

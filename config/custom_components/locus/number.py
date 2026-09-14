"""Number used for templates and other stuff."""

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    vacuum_battery = config_entry.data.get("auto_dock percent", 10)
    auto_dock_percent = ConfigInheritedNumber(
        config_entry, "Vacuum Dock %", vacuum_battery, 0, 100, 1
    )
    auto_dock_percent += 0
    # async_add_entities([auto_dock_percent])


class ConfigInheritedNumber(NumberEntity):
    """A standard custom number entity built for integrations."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        name: str,
        initial_value: float,
        min_value: float,
        max_value: float,
        step: float,
    ) -> None:
        """Initialize parameters safely inside standard init."""
        # Step 1: Assign local memory values
        super().__init__()
        self._value = initial_value

        # Step 2: Assign Home Assistant base attributes using safe _attr prefixes
        self._attr_unique_id = f"{config_entry.entry_id}_my_custom_number"
        self._attr_name = name
        self._attr_mode = "slider"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step

    @property
    def native_value(self) -> float:
        """Dynamically return the underlying value."""
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        """Update value when slider shifts."""
        self._value = value
        self.async_write_ha_state()

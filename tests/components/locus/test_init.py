"""Test the Locus integration."""

from unittest.mock import MagicMock, patch

from config.custom_components.locus import async_setup

from homeassistant.core import HomeAssistant


async def test_matter_stuck_error_maps_to_locus_database(
    hass: HomeAssistant,
) -> None:
    """Test a Matter vacuum error is mapped to the Locus database."""
    with patch("homeassistant.core.ServiceRegistry.async_register"):
        # Set up Locus so the database and state listener are registered.
        assert await async_setup(hass, {})

    # Fake the Matter entity registry entry.
    entity_entry = MagicMock()
    entity_entry.unique_id = "matter_RvcOperationalStateOperationalError_mock_vacuum"

    with (
        patch("config.custom_components.locus.er.async_get") as mock_entity_registry,
        patch(
            "config.custom_components.locus.persistent_notification.create"
        ) as mock_notification,
    ):
        mock_entity_registry.return_value.async_get.return_value = entity_entry

        # Simulate Home Assistant reporting a Matter vacuum error.
        hass.states.async_set(
            "sensor.mock_vacuum_operational_error",
            "stuck",
        )
        await hass.async_block_till_done()

        # The state change should have triggered Locus.
        mock_notification.assert_called_once()

        notification_call = mock_notification.call_args

        assert "Robot Vacuum Stuck" in notification_call.kwargs["title"]

        notification_message = notification_call.kwargs["message"]

        assert (
            "The robot vacuum is unable to move because it is trapped or blocked."
            in notification_message
        )

        assert "Remove any obstacles around the robot vacuum." in notification_message

        assert "Place the robot on a clear, level surface." in notification_message

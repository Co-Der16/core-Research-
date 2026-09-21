"""Translate Matter error values into Locus error codes."""

MATTER_ERROR_TO_LOCUS_CODE: dict[str, str] = {
    "stuck": "kStuck",
    "low_battery": "kLowBattery",
    "water_tank_empty": "kWaterTankEmpty",
    "water_tank_missing": "kWaterTankMissing",
    "water_tank_lid_open": "kWaterTankLidOpen",
    "dust_bin_missing": "kDustBinMissing",
    "dust_bin_full": "kDustBinFull",
    "unable_to_start_or_resume": "kUnableToStartOrResume",
    "unable_to_complete_operation": "kUnableToCompleteOperation",
    "command_invalid_in_state": "kCommandInvalidInState",
    "failed_to_find_charging_dock": "kFailedToFindChargingDock",
    "cannot_reach_target_area": "kCannotReachTargetArea",
    "dirty_water_tank_full": "kDirtyWaterTankFull",
    "dirty_water_tank_missing": "kDirtyWaterTankMissing",
    "wheels_jammed": "kWheelsJammed",
    "brush_jammed": "kBrushJammed",
    "navigation_sensor_obscured": "kNavigationSensorObscured",
    "mop_cleaning_pad_missing": "kMopCleaningPadMissing",
}


def matter_error_to_locus_code(matter_error: str) -> str | None:
    """Convert a Matter error value into a Locus error code."""
    return MATTER_ERROR_TO_LOCUS_CODE.get(matter_error)

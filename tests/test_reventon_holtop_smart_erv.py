"""Regression checks for the Reventon/Holtop Smart ERV Tuya profile.

The same product ID is reported by a Hyundai HRS-PRO250, but the
meaning of its temperature DPs still needs confirmation on hardware.
"""

import pytest

from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig
from custom_components.tuya_local.number import TuyaLocalNumber

from .helpers import assert_device_properties_set, mock_device


@pytest.mark.parametrize(
    ("name", "entity_type", "dp_id", "dp_type"),
    [
        ("Supply fan speed level (raw)", "sensor", "102", "string"),
        ("Exhaust fan speed level (raw)", "sensor", "103", "string"),
        ("Nine-step fan speed mode", "binary_sensor", "125", "boolean"),
        ("Fault code (raw)", "sensor", "119", "bitfield"),
    ],
)
def test_erv_extra_diagnostics_are_read_only(name, entity_type, dp_id, dp_type):
    """New diagnostics must use the observed DP with the correct type."""
    profile = TuyaDeviceConfig("reventon_holtop_smart_erv.yaml")
    matches = [entity for entity in profile.all_entities() if entity.name == name]

    assert len(matches) == 1
    entity = matches[0]
    assert entity.entity == entity_type
    assert entity.entity_category == "diagnostic"

    datapoints = list(entity.dps())
    assert len(datapoints) == 1
    assert datapoints[0].id == dp_id
    assert datapoints[0].rawtype == dp_type
    assert datapoints[0].name == "sensor"
    assert datapoints[0].force is False


@pytest.mark.parametrize(
    ("name", "dp_id"),
    [
        ("Supply fan speed (0-9)", "102"),
        ("Exhaust fan speed (0-9)", "103"),
    ],
)
@pytest.mark.asyncio
async def test_erv_speed_sliders_read_and_write_string_dps(mocker, name, dp_id):
    """0-9 UI levels must be sent as original Tuya string values."""
    profile = TuyaDeviceConfig("reventon_holtop_smart_erv.yaml")
    matches = [entity for entity in profile.all_entities() if entity.name == name]
    assert len(matches) == 1
    entity = matches[0]
    assert entity.entity == "number"
    assert entity.mode == "slider"

    device = mock_device({dp_id: "9", "125": True}, mocker)
    number = TuyaLocalNumber(device, entity)
    assert number.native_min_value == 0
    assert number.native_max_value == 9
    assert number.native_step == 1
    assert number.native_value == 9
    assert entity.available(device)

    async with assert_device_properties_set(device, {dp_id: "7"}):
        await number.async_set_native_value(7)

    # Do not offer an independent 0-9 control when the central unit
    # switches to the alternative three-step mode.
    device = mock_device({dp_id: "2", "125": False}, mocker)
    assert not entity.available(device)

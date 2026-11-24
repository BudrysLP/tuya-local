"""Regression checks for the Reventon/Holtop Smart ERV Tuya profile.

The same product ID is reported by a Hyundai HRS-PRO250, but the
meaning of its temperature DPs still needs confirmation on hardware.
"""

import pytest

from custom_components.tuya_local.helpers.device_config import TuyaDeviceConfig


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

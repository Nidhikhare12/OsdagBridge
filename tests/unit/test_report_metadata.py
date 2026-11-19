import pytest

from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    build_report_payload,
)
from osdagbridge.core.utils.common import KEY_TL_BRIDGE_TEMP_MIN


def build_payload(location, inputs=None, outputs=None):
    metadata = ReportMetadata("Test Bridge", location, "", "", "")
    request = ReportRequest(metadata, ReportOptions([], False, False, False), "", "report")
    return build_report_payload(request, inputs or {}, outputs or {})


@pytest.mark.parametrize("location", ["123", "Mumbai", "{broken", {"method": "map", "data": 42}])
def test_location_preserves_report_data(location):
    outputs = {"design_results": {"per_girder": {"G1": {"checks": ["example"]}}}}
    payload = build_payload(location, {"project_input": "retained"}, outputs)

    assert payload.inputs["project_input"] == "retained"
    assert payload.output_dict == outputs
    if isinstance(location, str):
        assert payload.metadata.project_location == location


def test_zero_metadata_values_are_retained():
    location = {
        "method": "custom_data",
        "data": {"latitude": 0, "longitude": 0},
        "weather_data": {"latitude": 20, "longitude": 30, "min_temp": 0},
    }
    payload = build_payload(location, outputs={KEY_TL_BRIDGE_TEMP_MIN: 0})

    assert payload.inputs["latitude"] == 0
    assert payload.inputs["longitude"] == 0
    assert payload.inputs["shade_temp_min"] == 0
    assert payload.inputs[KEY_TL_BRIDGE_TEMP_MIN] == 0


def test_explicit_zero_temperature_takes_precedence():
    payload = build_payload(
        "Mumbai",
        {KEY_TL_BRIDGE_TEMP_MIN: 0},
        {KEY_TL_BRIDGE_TEMP_MIN: 15},
    )
    assert payload.inputs[KEY_TL_BRIDGE_TEMP_MIN] == 0

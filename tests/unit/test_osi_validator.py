from osdagbridge.core.utils.osi_validator import validate_osi_inputs


def test_valid_osi_inputs_are_accepted():
    data = {
        "geometry.span": 30.0,
        "geometry.carriageway_width": 7.5,
        "geometry.skew_angle": 0.0,
    }

    result = validate_osi_inputs(data)

    assert result.is_valid is True
    assert result.errors == []


def test_non_numeric_span_is_rejected():
    data = {
        "geometry.span": "abcd",
        "geometry.carriageway_width": 7.5,
        "geometry.skew_angle": 0.0,
    }

    result = validate_osi_inputs(data)

    assert result.is_valid is False
    assert any("geometry.span" in error for error in result.errors)


def test_nested_osi_inputs_are_accepted():
    data = {
        "geometry": {
            "span": 30.0,
            "carriageway_width": 7.5,
            "skew_angle": 0.0,
        }
    }

    result = validate_osi_inputs(data)

    assert result.is_valid is True


def test_empty_osi_input_is_rejected():
    result = validate_osi_inputs({})

    assert result.is_valid is False
    assert any("valid input dictionary" in error for error in result.errors)

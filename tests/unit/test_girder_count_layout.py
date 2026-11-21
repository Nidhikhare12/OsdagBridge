"""
The girder layout must depend only on the current inputs, not on the order in
which they were typed (issue #112).

solve_extend_basic_input_dict() runs after every homepage edit, on Design, on
Save and on Load, always on the same dict. These tests replay those sequences.
"""

import contextlib
import copy
import io

import pytest

from osdagbridge.core.bridge_types.plate_girder.defaults import (
    BASIC_INPUT_DICT, solve_extend_basic_input_dict,
)
from osdagbridge.core.utils.common import (
    KEY_PROJECT_LOCATION, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_SKEW_ANGLE,
    KEY_INCLUDE_MEDIAN, KEY_FOOTPATH,
    KEY_TS_NO_OF_GIRDERS, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
)

LOCATION = {
    "data": {"district": "Mumbai(Bombay) (Santa Cruz)", "state": "Maharashtra"},
    "method": "location_name",
}


def _new_session(carriageway, span="40"):
    d = copy.deepcopy(BASIC_INPUT_DICT)
    d.update({KEY_PROJECT_LOCATION: LOCATION, KEY_SPAN: span,
              KEY_CARRIAGEWAY_WIDTH: carriageway, KEY_SKEW_ANGLE: "0"})
    return d


def _solve(d):
    with contextlib.redirect_stdout(io.StringIO()):  # the solver prints debug lines
        solve_extend_basic_input_dict(d)
    return (d[KEY_TS_NO_OF_GIRDERS],
            round(d[KEY_TS_GIRDER_SPACING], 4),
            round(d[KEY_TS_DECK_OVERHANG], 4))


def _fresh_layout(**inputs):
    d = _new_session(inputs.pop("carriageway"))
    d.update(inputs)
    return _solve(d)


def test_fresh_session_layout():
    # Span 40 m, carriageway 11 m, no median/footpath: 5 girders @ 2.38 m.
    assert _fresh_layout(carriageway="11") == (5, 2.38, 1.19)


@pytest.mark.parametrize("first_value", ["7.5", "5", "20"])
def test_correcting_the_carriageway_gives_the_fresh_layout(first_value):
    # Before the fix: 7.5 -> 11 gave 4 girders, 5 -> 11 gave 3, 20 -> 11 gave 9.
    d = _new_session(first_value)
    _solve(d)
    d[KEY_CARRIAGEWAY_WIDTH] = "11"
    assert _solve(d) == _fresh_layout(carriageway="11")


def test_unlock_after_a_design_and_change_inputs():
    # Design at span 30 / cw 7.5, unlock, change to span 40 / cw 11 (same dict).
    d = _new_session("7.5", span="30")
    _solve(d)        # homepage edit
    _solve(d)        # Design
    d[KEY_SPAN] = "40"
    _solve(d)
    d[KEY_CARRIAGEWAY_WIDTH] = "11"
    assert _solve(d) == _fresh_layout(carriageway="11")


@pytest.mark.parametrize("change", [
    {KEY_INCLUDE_MEDIAN: "Yes"},
    {KEY_FOOTPATH: "Both"},
], ids=["median", "footpath"])
def test_median_or_footpath_change_gives_the_fresh_layout(change):
    d = _new_session("11")
    _solve(d)
    d.update(change)
    assert _solve(d) == _fresh_layout(carriageway="11", **change)


def test_count_is_kept_when_the_deck_width_does_not_change():
    d = _new_session("11")
    _solve(d)
    d[KEY_SPAN] = "35"
    assert _solve(d)[0] == 5


def test_typical_section_count_is_kept_until_the_deck_width_changes():
    d = _new_session("11")
    _solve(d)
    # The user sets 6 girders in Additional Inputs > Typical Section (the dialog
    # re-solves the layout and stores the count with the unchanged deck width).
    d[KEY_TS_NO_OF_GIRDERS] = 6
    assert _solve(d)[0] == 6          # e.g. Design, Save or a span edit
    d[KEY_SPAN] = "35"
    assert _solve(d)[0] == 6
    # A new carriageway is a new deck: the layout is seeded again.
    d[KEY_CARRIAGEWAY_WIDTH] = "12"
    assert _solve(d) == _fresh_layout(carriageway="12")


def test_count_without_a_stored_width_is_kept():
    # A dict built by hand or through the API may give only the count.
    d = _new_session("11")
    d[KEY_TS_NO_OF_GIRDERS] = 4
    assert KEY_TS_OVERALL_WIDTH not in d or d[KEY_TS_OVERALL_WIDTH] in (None, "")
    assert _solve(d)[0] == 4

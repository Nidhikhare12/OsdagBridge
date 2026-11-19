import pytest

from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.report_generator import ReportDataBridge


@pytest.mark.parametrize("cover, expected", [(False, "FAIL"), (True, "PASS"), (None, "Unavailable")])
def test_deck_detailing_displays_cover_verdict_without_unconditional_pass(cover, expected):
    from osdagbridge.core.utils.common import KEY_DD_COVER_OK, KEY_DD_MIN_COVER

    bridge = ReportDataBridge({"deck_report_values": {
        KEY_DD_COVER_OK: cover, KEY_DD_MIN_COVER: 75,
    }}, {}, None)
    chapter = ch5_design_checks([], bridge)
    detailing = chapter.split("Reinforcement Detailing Summary", 1)[1].split(
        "Cross Bracing Design", 1
    )[0]
    cover_row = next(row for row in detailing.splitlines() if row.startswith("Clear Cover"))
    assert expected in cover_row
    assert "All reinforcement provisions satisfy" not in detailing
    assert "Unavailable" in detailing

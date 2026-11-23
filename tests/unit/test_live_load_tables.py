"""Tests for the Chapter 3 live-load tables (task item 3)."""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from pathlib import Path

import pytest

from osdagbridge.core.reports import live_load_tables as llt
from osdagbridge.core.reports import styles
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.utils import common as keys
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def _inputs(**extra: object) -> dict:
    data: dict = {keys.KEY_SPAN: "30"}
    data.update(extra)
    return data


ALL = {
    keys.KEY_LL_IRC_CLASS_A: True,
    keys.KEY_LL_IRC_70R_WHEELED: True,
    keys.KEY_LL_IRC_70R_TRACKED: True,
    keys.KEY_LL_IRC_AA_WHEELED: True,
    keys.KEY_LL_IRC_CLASS_SV: True,
    keys.KEY_LL_CUSTOM_VEHICLES: [{"name": "My Crane"}],
}


class TestVehicleRows:
    @pytest.fixture
    def rows(self) -> dict:
        return {r.name: r for r in llt.vehicle_rows(_inputs(**ALL))}

    def test_rows_follow_ui_selection_order(self) -> None:
        names = [r.name for r in llt.vehicle_rows(_inputs(**ALL))]
        assert names == ["Class A", "Class 70R (Wheeled)",
                         "Class 70R (Tracked)", "Class AA (Wheeled)",
                         "Class SV", "My Crane"]

    def test_unselected_vehicles_are_absent(self) -> None:
        rows = llt.vehicle_rows(_inputs(**{keys.KEY_LL_IRC_CLASS_A: True}))
        assert [r.name for r in rows] == ["Class A"]

    def test_class_a_values(self, rows: dict) -> None:
        a = rows["Class A"]
        assert a.total_load_kn == pytest.approx(543.474)
        assert a.impact_factor == pytest.approx(1.207)
        assert a.braking_considered is True
        assert a.braking_value_kn == pytest.approx(0.2 * 543.474)
        assert a.braking_eccentricity_m == pytest.approx(1.2)

    def test_70r_values(self, rows: dict) -> None:
        wheeled, tracked = rows["Class 70R (Wheeled)"], rows["Class 70R (Tracked)"]
        assert wheeled.total_load_kn == pytest.approx(981.0)
        assert tracked.total_load_kn == pytest.approx(686.82, abs=0.01)
        assert wheeled.impact_factor == pytest.approx(1.1)

    def test_special_vehicle_has_no_braking_or_impact(self, rows: dict) -> None:
        sv = rows["Class SV"]
        assert sv.total_load_kn == pytest.approx(3776.85)
        assert sv.braking_considered is False
        assert sv.braking_value_kn is None
        assert sv.braking_eccentricity_m is None
        assert sv.impact_factor is None

    def test_unknown_data_is_none_not_invented(self, rows: dict) -> None:
        aa = rows["Class AA (Wheeled)"]
        assert aa.total_load_kn is None
        assert aa.braking_value_kn is None
        crane = rows["My Crane"]
        assert dataclasses.astuple(crane)[1:] == (None,) * 5

    @pytest.mark.parametrize("span", [None, "", "abc"])
    def test_missing_or_bad_span_removes_impact_only(self, span) -> None:
        inputs = _inputs(**ALL)
        inputs[keys.KEY_SPAN] = span
        rows = llt.vehicle_rows(inputs)
        assert all(r.impact_factor is None for r in rows)
        assert rows[0].total_load_kn is not None

    def test_empty_selection(self) -> None:
        assert llt.vehicle_rows({}) == []

    def test_custom_vehicle_as_plain_string_and_junk(self) -> None:
        rows = llt.vehicle_rows(
            {keys.KEY_LL_CUSTOM_VEHICLES: ["Crane", {"name": ""}, 5, None]})
        assert [r.name for r in rows] == ["Crane"]

    def test_does_not_depend_on_the_broken_backend_braking_function(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        def broken(*_a: object) -> float:
            raise UnboundLocalError("backend bug")
        monkeypatch.setattr(IRC6_2017, "cl_211_2_braking_force", broken)
        assert llt.vehicle_rows(_inputs(**ALL))[0].braking_value_kn


class TestFootway:
    def test_irc_mode(self) -> None:
        rows = llt.footway_rows(
            {keys.KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6"})
        assert rows[0][1] == "4.905"
        assert rows[1] == ("Basis", "IRC 6", "Cl. 206.1")

    def test_user_defined_value(self) -> None:
        rows = llt.footway_rows({keys.KEY_LL_FOOTPATH_PRESSURE_MODE: "Custom",
                                 keys.KEY_LL_FOOTPATH_PRESSURE_VALUE: "5.5"})
        assert rows[0][1] == "5.5"
        assert rows[1][1] == "User defined"

    def test_special_characters_are_escaped(self) -> None:
        rows = llt.footway_rows({keys.KEY_LL_FOOTPATH_PRESSURE_VALUE: "5_5%"})
        assert r"\%" in rows[0][1]

    def test_no_footway_load(self) -> None:
        assert llt.footway_rows({}) == []
        assert "Not applicable" in llt.footway_table([])


class TestLatex:
    def test_two_separate_tables(self) -> None:
        tex = llt.live_load_tables(_inputs(**ALL))
        assert tex.count(r"\begin{longtable}") == 2
        assert "Vehicles (IRC 6)" in tex and "Footway" in tex
        assert "Vehicles Considered" not in tex

    def test_vehicle_table_structure(self) -> None:
        tex = llt.vehicle_table(llt.vehicle_rows(_inputs(**ALL)))
        assert r"\multicolumn{3}{c|}{\textbf{Braking Load}}" in tex
        assert r"\cline{4-6}" in tex
        assert "Total Load (kN)" in tex and "Eccentricity (m)" in tex
        assert "Class A & 543.5 & 1.207 & Yes & 108.7 & 1.20" in tex
        assert "Class SV & 3776.8 & -- & No & -- & --" in tex
        assert "centrifugal" in tex.lower()

    def test_no_vehicles_message(self) -> None:
        assert "No live-load vehicle selected" in llt.vehicle_table([])

    def test_layout_comes_from_styles(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            styles, "LOAD_TABLES",
            dataclasses.replace(styles.LOAD_TABLES, placeholder="n/a"))
        tex = llt.vehicle_table(llt.vehicle_rows(_inputs(**ALL)))
        assert "& n/a &" in tex

    def test_rows_use_the_shared_row_gap_macro(self) -> None:
        tex = llt.vehicle_table(llt.vehicle_rows(_inputs(**ALL)))
        assert r"\\[\rowgap]" in tex and r"\\[6pt]" not in tex
        assert r"\colunit" in tex

    def test_chapter_3_uses_the_new_tables(self) -> None:
        tex = ch3_loads(_inputs(**ALL))
        assert "Live Loads (LL) --- Vehicles (IRC 6)" in tex
        assert "Live Loads (LL) --- Footway" in tex
        assert "Vehicles Considered" not in tex

    @pytest.mark.skipif(shutil.which("pdflatex") is None,
                        reason="pdflatex not installed")
    def test_chapter_3_compiles_cleanly(self, tmp_path: Path) -> None:
        from osdagbridge.core.reports.latex_tables import normalize_longtables
        from osdagbridge.core.reports.report_generator import preamble
        tex = (preamble("T", "J", "d")
               + normalize_longtables(ch3_loads(_inputs(**ALL)))
               + "\n\\end{document}\n")
        (tmp_path / "doc.tex").write_text(tex, encoding="utf-8")
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "doc.tex"],
                           cwd=tmp_path, capture_output=True, check=False)
        log = (tmp_path / "doc.log").read_text(errors="ignore")
        assert sum(ln.startswith("!") for ln in log.splitlines()) == 0

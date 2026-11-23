"""Task I - double-click editing of the 2D CAD dimension labels."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH, KEY_MP_CB_SPACING, KEY_TS_NO_OF_GIRDERS,
)


@pytest.fixture
def views(window, basic_inputs, pump):
    cad = window.cad_comp_widget
    cs, tv = cad.cross_section_widget, cad.top_view_widget
    # The start-up zoom depends on the window layout, which differs between
    # platforms (fonts); fit both views so every test sees the same drawing.
    for view in (cs, tv):
        view.show_span_values = True
        view.show_carriageway_values = True
        view.fit_to_screen()
    pump(200)
    return cs, tv


@pytest.fixture
def cad(window, pump):
    class Driver:
        def region(self, view, key):
            view.repaint()
            for rect, k in view._label_regions:
                if k == key:
                    return rect
            raise AssertionError(f"label {key} not drawn")

        def double_click(self, view, key):
            p = self.region(view, key).center().toPoint()
            QTest.mouseMove(view, p)
            pump(50)
            QTest.mouseDClick(view, Qt.LeftButton, Qt.NoModifier, p)
            pump(100)
            return view._label_editor

        def edit(self, view, key, text, finish=Qt.Key_Return):
            editor = self.double_click(view, key)
            assert editor is not None, f"no editor opened for {key}"
            editor.selectAll()
            QTest.keyClicks(editor, text)
            QTest.keyClick(editor, finish)
            pump(300)
    return Driver()


def test_editable_and_locked_labels_are_registered(views):
    cs, tv = views
    cs.repaint(); tv.repaint()
    cs_keys = {k for _, k in cs._label_regions}
    tv_keys = {k for _, k in tv._label_regions}
    assert {KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
            KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH} <= cs_keys
    assert {KEY_SPAN, KEY_MP_CB_SPACING, KEY_TS_GIRDER_SPACING} <= tv_keys


def test_carriageway_edit_updates_dict_dock_and_cad(window, views, cad, basic_inputs):
    cs, _ = views
    cad.edit(cs, KEY_CARRIAGEWAY_WIDTH, "9.5")
    assert float(window.input_dict[KEY_CARRIAGEWAY_WIDTH]) == pytest.approx(9.5)
    assert basic_inputs(KEY_CARRIAGEWAY_WIDTH).text() == "9.5"
    assert cs.params["carriageway_width"] == pytest.approx(9500)


def test_span_edit_from_top_view(window, views, cad, basic_inputs):
    _, tv = views
    cad.edit(tv, KEY_SPAN, "40")
    assert float(window.input_dict[KEY_SPAN]) == pytest.approx(40)
    assert basic_inputs(KEY_SPAN).text() == "40"
    assert tv.params["span_length"] == pytest.approx(40000)


def test_girder_spacing_keeps_girder_count_and_rederives_overhang(window, views, cad):
    cs, _ = views
    cad.edit(cs, KEY_TS_DECK_THICKNESS, "250")       # forces the layout to be solved
    d = window.input_dict
    n, width = int(d[KEY_TS_NO_OF_GIRDERS]), d[KEY_TS_OVERALL_WIDTH]
    cad.edit(cs, KEY_TS_GIRDER_SPACING, "2.2")
    assert float(d[KEY_TS_GIRDER_SPACING]) == pytest.approx(2.2)
    assert int(d[KEY_TS_NO_OF_GIRDERS]) == n
    assert (n - 1) * 2.2 + 2 * float(d[KEY_TS_DECK_OVERHANG]) == pytest.approx(float(width))
    assert cs.params["girder_spacing"] == pytest.approx(2200)


def test_deck_thickness_edit(window, views, cad):
    cs, _ = views
    cad.edit(cs, KEY_TS_DECK_THICKNESS, "300")
    assert float(window.input_dict[KEY_TS_DECK_THICKNESS]) == pytest.approx(300)
    assert cs.params["deck_thickness"] == pytest.approx(300)


@pytest.mark.parametrize("view_index, key, text", [
    (0, KEY_TS_DECK_THICKNESS, "50"),        # below the validator minimum
    (0, KEY_TS_GIRDER_SPACING, "9"),         # leaves a negative overhang
    (1, KEY_SPAN, "80"),                     # outside the span range
])
def test_invalid_values_are_rejected_and_previous_value_kept(window, views, cad, messages,
                                                             view_index, key, text):
    view = views[view_index]
    cad.edit(views[0], KEY_TS_DECK_THICKNESS, "260")     # solve the layout first
    before = window.input_dict.get(key)
    n = len(messages)
    cad.edit(view, key, text)
    assert window.input_dict.get(key) == before
    assert any("previous value has been kept" in m for m in messages.since(n))


def test_escape_cancels_and_focus_out_commits(window, views, cad, basic_inputs, pump):
    cs, _ = views
    cad.edit(cs, KEY_TS_DECK_THICKNESS, "280")
    cad.edit(cs, KEY_TS_DECK_THICKNESS, "400", finish=Qt.Key_Escape)
    assert float(window.input_dict[KEY_TS_DECK_THICKNESS]) == pytest.approx(280)
    assert cs._label_editor is None

    editor = cad.double_click(cs, KEY_TS_DECK_THICKNESS)
    editor.selectAll()
    QTest.keyClicks(editor, "275")
    basic_inputs(KEY_SPAN).setFocus()                # click away
    pump(300)
    assert float(window.input_dict[KEY_TS_DECK_THICKNESS]) == pytest.approx(275)


@pytest.mark.parametrize("view_index, key", [
    (0, KEY_TS_DECK_OVERHANG), (0, KEY_TS_OVERALL_WIDTH), (1, KEY_MP_CB_SPACING),
])
def test_locked_labels_do_not_open_an_editor(views, cad, view_index, key):
    assert cad.double_click(views[view_index], key) is None


def test_no_editing_while_inputs_are_locked(window, views, cad, messages):
    cs, _ = views
    window.input_dock.is_locked = True
    try:
        assert cad.double_click(cs, KEY_TS_DECK_THICKNESS) is None
    finally:
        window.input_dock.is_locked = False


def test_cad_edits_survive_a_span_change(window, views, cad, basic_inputs, type_into, pump):
    cs, _ = views
    cad.edit(cs, KEY_TS_GIRDER_SPACING, "2.2")
    cad.edit(cs, KEY_TS_DECK_THICKNESS, "300")
    type_into(basic_inputs(KEY_SPAN), "40")           # re-defaults additional inputs
    pump(300)
    d = window.input_dict
    assert float(d[KEY_SPAN]) == pytest.approx(40)
    assert float(d[KEY_TS_GIRDER_SPACING]) == pytest.approx(2.2)
    assert float(d[KEY_TS_DECK_THICKNESS]) == pytest.approx(300)
    assert cs.params["girder_spacing"] == pytest.approx(2200)


def test_cad_girder_spacing_is_resolved_against_a_new_carriageway(window, views, cad,
                                                                  basic_inputs, type_into, pump):
    cs, _ = views
    cad.edit(cs, KEY_TS_GIRDER_SPACING, "2.2")
    type_into(basic_inputs(KEY_CARRIAGEWAY_WIDTH), "8.5")
    pump(300)
    d = window.input_dict
    n = int(d[KEY_TS_NO_OF_GIRDERS])
    assert float(d[KEY_TS_GIRDER_SPACING]) == pytest.approx(2.2)
    assert (n - 1) * 2.2 + 2 * float(d[KEY_TS_DECK_OVERHANG]) == pytest.approx(float(d[KEY_TS_OVERALL_WIDTH]))


def _overlaps(view):
    view.repaint()
    rects = [(r, k) for r, k in view._label_regions]
    clashes = []
    for i, (a, ka) in enumerate(rects):
        for b, kb in rects[i + 1:]:
            if ka != kb and a.intersects(b):
                clashes.append((ka, kb))
    return rects, clashes


@pytest.mark.parametrize("zoom", [1.0, 0.5])
def test_clickable_labels_never_overlap(views, pump, zoom):
    """Overlapping labels make a double-click ambiguous (seen with Linux fonts
    on a small drawing), so check the fitted view and a zoomed-out one."""
    for view in views:
        view.zoom_level *= zoom
        view._update_widget_size()
        pump(100)
        rects, clashes = _overlaps(view)
        assert rects, "no labels registered"
        assert all(r.width() > 8 for r, _ in rects), "degenerate click target"
        assert clashes == [], clashes


def test_when_labels_do_overlap_the_visible_one_is_edited(views):
    """Far zoomed out, labels can touch (the original drawing's own labels do).
    Labels have opaque backgrounds, so the one painted last is the one you see,
    and that is the one a double-click must pick."""
    from PySide6.QtCore import QPointF, QRectF
    cs, _ = views
    cs._label_regions = [(QRectF(0, 0, 100, 20), KEY_TS_DECK_OVERHANG),
                         (QRectF(50, 5, 100, 20), KEY_TS_GIRDER_SPACING)]
    assert cs._label_at(QPointF(75, 10))[1] == KEY_TS_GIRDER_SPACING      # both: top wins
    assert cs._label_at(QPointF(20, 10))[1] == KEY_TS_DECK_OVERHANG       # only the lower one
    assert cs._label_at(QPointF(300, 300))[1] is None

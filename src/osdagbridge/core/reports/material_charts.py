"""Material quantity bar charts for Chapter 7 (values come from the BOQ keys)."""
import logging
import os
import tempfile

from osdagbridge.core.reports import styles as S

log = logging.getLogger(__name__)


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _steel_items(d):
    items = []
    g = _num(d.get("steel_girders_wt_total"))
    if g is not None:
        items.append(("Girders", g))
    parts = [_num(d.get(k)) for k in ("bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    parts = [p for p in parts if p is not None]
    if parts:
        items.append(("Cross Bracing", sum(parts)))
    return items


def _label(ax, bars, vals, fmt="{:.2f}"):
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=8)


def _steel_chart(items, path):
    from matplotlib.figure import Figure
    C = S.CHART
    fig = Figure(figsize=C["figsize"], dpi=C["dpi"])
    ax = fig.subplots()
    vals = [v for _, v in items]
    bars = ax.bar([n for n, _ in items], vals, color=C["bar_colors"][:len(items)], width=0.5)
    ax.set_ylabel("Structural Steel Weight (MT)")
    ax.set_ylim(0, max(vals) * 1.2 if max(vals) > 0 else 1)
    _label(ax, bars, vals)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=C["dpi"], bbox_inches="tight")


def _conc_rebar_chart(conc, rebar, path):
    from matplotlib.figure import Figure
    C = S.CHART
    fig = Figure(figsize=C["figsize"], dpi=C["dpi"])
    a1, a2 = fig.subplots(1, 2)
    b1 = a1.bar(["Deck Concrete"], [conc], color=C["bar_colors"][0], width=0.4)
    a1.set_ylabel("Concrete Volume (m$^3$)")
    a1.set_ylim(0, conc * 1.2 if conc > 0 else 1)
    _label(a1, b1, [conc])
    b2 = a2.bar(["Reinforcement Steel"], [rebar], color=C["bar_colors"][2], width=0.4)
    a2.set_ylabel("Reinforcement Weight (MT)")
    a2.set_ylim(0, rebar * 1.2 if rebar > 0 else 1)
    _label(a2, b2, [rebar])
    for a in (a1, a2):
        a.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=C["dpi"], bbox_inches="tight")


def make_chart_files(d, outdir):
    files = []
    steel = _steel_items(d)
    if steel:
        p = os.path.join(outdir, "qty_steel.png")
        _steel_chart(steel, p)
        files.append((p, "Structural steel quantity (MT) by component"))
    conc, rebar = _num(d.get("concrete_deck_vol_total")), _num(d.get("rebar_deck_wt_total"))
    if conc is not None and rebar is not None:
        p = os.path.join(outdir, "qty_conc_rebar.png")
        _conc_rebar_chart(conc, rebar, p)
        files.append((p, "Deck concrete volume (m$^3$) and reinforcement steel weight (MT)"))
    return files


def material_charts_latex(input_dict):
    try:
        outdir = tempfile.mkdtemp(prefix="osdagqty")
        out = []
        for path, cap in make_chart_files(input_dict, outdir):
            out.append(
                "\\needspace{14\\baselineskip}\n\\begin{figure}[H]\n\\centering\n"
                "\\includegraphics[width=" + S.FIGURE_WIDTH + "]{" + path.replace("\\", "/") + "}\n"
                "\\caption{" + cap + "}\n\\end{figure}\n"
            )
        return "\n\\vspace{1em}\n" + "\n".join(out) if out else ""
    except Exception as exc:
        log.warning("Material charts skipped: %s", exc)
        return ""

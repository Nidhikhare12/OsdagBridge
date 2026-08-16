import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Tuple

def generate_ur_plots(bridge) -> Tuple[bytes, bytes, bytes, bytes]:
    """Generate UR detail plots for each category, and  returning their PNG bytes."""
    
    # Extracting the raw utilisation ratios
    pg_522 = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}

    def _get_dkv(key, default=0.0):
        v = deck_rpt.get(key)
        try:
            return float(v) if v not in (None, "") else default
        except (TypeError, ValueError):
            return default

    def _get_girder_ur(check_ids):
        best_ur = 0.0
        for g, gd in pg_522.items():
            if str(g).startswith("EB"): continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    best_ur = max(best_ur, float(chk.get("dcr") or 0.0))
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"): continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        best_ur = max(best_ur, float(chk.get("dcr") or 0.0))
        return best_ur

    def _get_deck_ur(dem_key, cap_key):
        dem = _get_dkv(dem_key)
        cap = _get_dkv(cap_key)
        return (dem / cap) if cap > 0 else 0.0

    def _get_cb_ur(force_type):
        best_ur = 0.0
        for pair in bridge.get_cb_pairs():
            for member in ("diagonal", "chord"):
                eff = bridge.get_cb_efficiency(pair, member, force_type)
                try:
                    best_ur = max(best_ur, float(eff))
                except:
                    pass
        return best_ur

    def _get_cb_slender_ur():
        best_ur = 0.0
        for pair in bridge.get_cb_pairs():
            for member in ("diagonal", "chord"):
                try:
                    sf = float(bridge.get_cb_slenderness(pair, member))
                    lim = 400.0 if member == "chord" else 250.0
                    best_ur = max(best_ur, sf / lim)
                except:
                    pass
        return best_ur

    # Deck keys that is used in chap5.py
    _wk_lim = _get_dkv('deck_slab.crack_width_limit')
    _dk_wks = [_get_dkv('deck_slab.crack_width_bot'), _get_dkv('deck_slab.crack_width_top')]
    if bool(deck_rpt.get('deck_slab.has_overhang')):
        _dk_wks.append(_get_dkv('deck_slab.crack_width_oh'))
    _dk_gov_wk = max(_dk_wks) if _dk_wks else 0.0
    crack_ur = (_dk_gov_wk / _wk_lim) if _wk_lim > 0 else 0.0


    detail_data = {
        "Girder": {
            "Moment": _get_girder_ur({1}),
            "Shear": _get_girder_ur({2}),
            "LTB": _get_girder_ur({5}),
            "Deflection": _get_girder_ur({13, 14}),
            "Stress": _get_girder_ur({11}),
            "Fatigue": _get_girder_ur({8, 9}),
        },
        "Deck": {
            "Flex (Sag)": _get_deck_ur('deck_slab.m_uls_sag', 'deck_slab.mu_bot'),
            "Flex (Hog)": _get_deck_ur('deck_slab.m_uls_hog', 'deck_slab.mu_top'),
            "Overhang": _get_deck_ur('deck_slab.m_uls_oh', 'deck_slab.mu_oh'),
            "Punch Shear": _get_deck_ur('deck_slab.punch_ved', 'deck_slab.vrd_c_mpa'),
            "Beam Shear": _get_deck_ur('deck_slab.shear_ved', 'deck_slab.shear_vrdc'),
            "Crack": crack_ur,
        },
        "Cross Bracing": {
            "Compression": _get_cb_ur("compression"),
            "Tension": _get_cb_ur("tension"),
            "Slenderness": _get_cb_slender_ur(),
        },
        "End Diaphragm": {}
    }

   
    from osdagbridge.core.utils.common import KEY_MP_ED_TYPE
    _ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            _ed_type = str(_v)
            break
    _ed_is_cb = "brac" in _ed_type.strip().lower()
    if _ed_is_cb:
        detail_data["End Diaphragm"] = {
            "Moment": _get_cb_ur("compression"),
            "Shear": _get_cb_ur("tension")
        }
    else:
        detail_data["End Diaphragm"] = {"Check": 0.0} # Placeholder

    # Helper to plot bars
    def plot_bars(ax, labels, values, title):
        colors = ['red' if v > 1.0 else '#91B014' for v in values] 
        bars = ax.bar(labels, values, color=colors, edgecolor='black', zorder=3)
        ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5, zorder=2)
        ax.set_ylabel('Utilization Ratio (UR)', fontsize=12)
        ax.set_title(title, fontweight='bold', fontsize=18, pad=20)
        ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
        
        ax.tick_params(axis='both', which='major', labelsize=11)
        
        # Adjust Y limit if max is less than 1.2
        max_val = max(values) if values else 0
        if max_val < 1.2:
            ax.set_ylim(0, 1.2)
        else:
            ax.set_ylim(0, max_val * 1.1)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9)

    #Generate individual charts for each category
    def create_single_chart(category, checks):
        fig, ax = plt.subplots(figsize=(10, 5)) 
        labels = list(checks.keys())
        values = list(checks.values())
        plot_bars(ax, labels, values, f'{category} Checks')
        ax.tick_params(axis='x', rotation=0) 
        if len(labels) > 4:
            ax.tick_params(axis='x', rotation=15)
            
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300)
        plt.close(fig)
        return buf.getvalue()

    detail_bytes_girder = create_single_chart("Girder", detail_data["Girder"])
    detail_bytes_deck = create_single_chart("Deck", detail_data["Deck"])
    detail_bytes_cb = create_single_chart("Cross Bracing", detail_data["Cross Bracing"])
    detail_bytes_ed = create_single_chart("End Diaphragm", detail_data["End Diaphragm"])

    return detail_bytes_girder, detail_bytes_deck, detail_bytes_cb, detail_bytes_ed

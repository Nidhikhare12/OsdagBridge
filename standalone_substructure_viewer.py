"""
Standalone substructure viewer -- independent of the full OsdagBridge GUI.

Renders pier + pier cap + pile cap + piles (with rebar, semi-transparent
concrete) using the exact same builder.py functions the real app uses, so
this is a legitimate backup if the full app keeps hitting missing
dependencies unrelated to our work.

Run with:
    conda activate osdagbridge-env
    python standalone_substructure_viewer.py

Place this file anywhere in the repo (e.g. tools/) -- it only imports from
the four builder.py files, nothing else from the app.
"""
import sys
import importlib.util


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ADAPT these paths if your repo layout differs.
PIER_BUILDER_PATH = "src/osdagbridge/core/bridge_components/sub_structure/pier/builder.py"
PIER_CAP_BUILDER_PATH = "src/osdagbridge/core/bridge_components/sub_structure/pier_cap/builder.py"
PILE_CAP_BUILDER_PATH = "src/osdagbridge/core/bridge_components/foundation/pile_cap/builder.py"
PILE_BUILDER_PATH = "src/osdagbridge/core/bridge_components/foundation/pile/builder.py"


def main():
    pier_b = _load_module("pier_builder", PIER_BUILDER_PATH)
    cap_b = _load_module("pier_cap_builder", PIER_CAP_BUILDER_PATH)
    pcap_b = _load_module("pile_cap_builder", PILE_CAP_BUILDER_PATH)
    pile_b = _load_module("pile_builder", PILE_BUILDER_PATH)

    from OCC.Display.SimpleGui import init_display
    from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

    display, start_display, add_menu, add_function_to_menu = init_display()

    # --- Build the full stack, same Z-offset logic as the real pipeline ---
    deck_soffit_z = 0.0

    cap = cap_b.build_pier_cap_geometry(
        top_width=3000, bottom_width=1200, depth=600, length=6000,
        top_center=(0.0, -3000.0, deck_soffit_z),
    )
    pier = pier_b.build_pier_geometry(
        diameter=800, height=3000,
        top_center=(0.0, 0.0, cap["pier_cap_bottom_z"]),
    )
    pcap = pcap_b.build_pile_cap_geometry(
        length=2200, width=1200, depth=600,
        top_center=(0.0, 0.0, pier["pier_bottom_z"]),
    )
    piles = pile_b.build_pile_group_geometry(
        diameter=400, length=5000, spacing=600,
        top_center=(0.0, 0.0, pcap["pile_cap_bottom_z"]),
    )

    CONCRETE_COLOR = Quantity_Color(0.75, 0.74, 0.70, Quantity_TOC_RGB)
    REBAR_COLOR = Quantity_Color(0.55, 0.55, 0.58, Quantity_TOC_RGB)
    CONCRETE_TRANSPARENCY = 0.35  # matches the task's semi-transparent requirement

    def show_concrete(shapes):
        for s in shapes:
            display.DisplayShape(s, color=CONCRETE_COLOR, transparency=CONCRETE_TRANSPARENCY, update=False)

    def show_rebar(shapes):
        for s in shapes:
            display.DisplayShape(s, color=REBAR_COLOR, transparency=0.0, update=False)

    show_concrete(cap["pier_cap_concrete"])
    show_rebar(cap["pier_cap_rebar"])
    show_concrete(pier["pier_concrete"])
    show_rebar(pier["pier_rebar"])
    show_concrete(pcap["pile_cap_concrete"])
    show_rebar(pcap["pile_cap_rebar"])
    show_concrete(piles["pile_concrete"])
    show_rebar(piles["pile_rebar"])

    display.FitAll()
    start_display()


if __name__ == "__main__":
    main()
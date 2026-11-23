"""Parametric inputs for the OsdagBridge substructure (all lengths in mm).

Coordinate system (same as superstructure):
  X = longitudinal (span), Y = transverse (deck width), Z = vertical.
  Origin = centre of span at deck level, so substructure lies at Z < 0.
"""
from dataclasses import dataclass


@dataclass
class SubstructureParams:
    # --- Piers (circular columns) ---
    pier_diameter: float = 800
    pier_height: float = 3000
    pier_y_positions: tuple = (-2000, 2000)   # one column per entry (transverse)
    pier_x: float = 0.0                       # longitudinal location of the pier line

    # --- Pier cap (trapezoidal / hammerhead), profile in XZ, extruded along Y ---
    pier_cap_top_width: float = 3000
    pier_cap_bottom_width: float = 1200
    pier_cap_depth: float = 600
    pier_cap_length: float = 8000             # set equal to deck width
    superstructure_depth: float = 1500        # deck level -> top of pier cap (girder + bearing)

    # --- Pile cap (rectangular prism, one per pier) ---
    pile_cap_length: float = 2200             # along X
    pile_cap_width: float = 1200              # along Y
    pile_cap_depth: float = 600

    # --- Piles (2 x 2 grid under each pile cap) ---
    n_piles_per_cap: int = 4
    pile_diameter: float = 400
    pile_length: float = 5000
    pile_spacing: float = 600                 # centre-to-centre
    pile_main_bars: int = 6

    # --- Reinforcement ---
    rebar_main_diameter: float = 16
    rebar_spacing_longitudinal: float = 150
    rebar_transverse_diameter: float = 8
    rebar_spacing_transverse: float = 200
    rebar_cover: float = 40

    # --- Display ---
    concrete_opacity: float = 0.35

    # ---- derived vertical levels (Z) ----
    @property
    def cap_top_z(self): return -self.superstructure_depth
    @property
    def cap_bot_z(self): return self.cap_top_z - self.pier_cap_depth
    @property
    def pier_top_z(self): return self.cap_bot_z
    @property
    def pier_bot_z(self): return self.pier_top_z - self.pier_height
    @property
    def pilecap_top_z(self): return self.pier_bot_z
    @property
    def pilecap_bot_z(self): return self.pilecap_top_z - self.pile_cap_depth
    @property
    def pile_top_z(self): return self.pilecap_bot_z
    @property
    def pile_bot_z(self): return self.pile_top_z - self.pile_length

    def pile_offsets(self):
        """(dx, dy) of piles relative to pile-cap centre; default 2x2 grid."""
        s = self.pile_spacing / 2.0
        if self.n_piles_per_cap == 4:
            return [(-s, -s), (s, -s), (-s, s), (s, s)]
        n = int(round(self.n_piles_per_cap ** 0.5))
        if n * n != self.n_piles_per_cap:
            raise ValueError("n_piles_per_cap must be a perfect square")
        c = (n - 1) * self.pile_spacing / 2.0
        return [(i * self.pile_spacing - c, j * self.pile_spacing - c)
                for i in range(n) for j in range(n)]

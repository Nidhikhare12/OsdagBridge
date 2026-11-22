# OsdagBridge Input Parameters & Specification Reference

This document serves as the master engineering reference for all parameters accepted by the OsdagBridge Plate Girder module, their canonical dictionary keys, permitted numerical ranges, physical units, default values, and codal basis.

---

## 1. Basic Geometric Parameters

| Parameter Name | Dictionary Key | Data Type | Default | Permissible Range | Unit | Codal / Design Basis |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Span Length** | `geometry.span` | `float` | `25.0` | $12.0 \le L \le 45.0$ | $\text{m}$ | Software scope limitation for plate girders |
| **Carriageway Width** | `geometry.carriageway_width` | `float` | `7.5` | $4.25 \le W \le 24.0$ | $\text{m}$ | IRC:5–2015 Clause 104.3.1 |
| **Include Median** | `geometry.include_median` | `str` | `"No"` | `{"Yes", "No"}` | — | IRC:5 median lane configuration switch |
| **Footpath** | `geometry.footpath` | `str` | `"No"` | `{"Yes", "No"}` | — | Pedestrian walkway provision |
| **Skew Angle** | `geometry.skew_angle` | `float` | `0.0` | $-60.0 \le \theta \le 60.0$ | $\text{deg}$ | IRC:24–2010 Clause 503; structural limit |
| **Design Mode** | `geometry.design_mode` | `str` | `"Auto"` | `{"Auto", "Custom"}` | — | Sizing mode selector |

---

## 2. Structural Steel Material Properties

### Standard Presets
- Available presets: `E250`, `E300`, `E350`, `E410`, `E450`, `Custom`.
- Standard values comply with IS 2062:2011 / IS 800:2007.

### Custom Steel Parameter Limits (Girder, Cross Bracing, End Diaphragm)

| Parameter Name | Canonical Key Pattern (`<member>` = `girder`, `cross_bracing`, `end_diaphragm`) | Data Type | Default (E350) | Permissible Range | Unit |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Yield Strength ($f_y$)** | `material.<member>.fy` | `float` | `350.0` | $100.0 \le f_y \le 1200.0$ | $\text{MPa}$ |
| **Ultimate Strength ($f_u$)**| `material.<member>.fu` | `float` | `490.0` | $100.0 \le f_u \le 1500.0$ | $\text{MPa}$ |
| **Modulus of Elasticity ($E$)**| `material.<member>.e` | `float` | `200.0` | $100.0 \le E \le 300.0$ | $\text{GPa}$ |
| **Modulus of Rigidity ($G$)** | `material.<member>.g` | `float` | `76.9` | $30.0 \le G \le 120.0$ | $\text{GPa}$ |
| **Poisson's Ratio ($\nu$)** | `material.<member>.poisson` | `float` | `0.30` | $0.1 \le \nu \le 0.4$ | — |
| **Thermal Expansion ($\alpha$)**| `material.<member>.thermal` | `float` | `1.2e-5` | $5.0\times 10^{-6} \le \alpha \le 2.5\times 10^{-5}$ | $/\text{^\circ C}$ |
| **Weight Density ($\rho$)** | `material.<member>.density` | `float` | `78.5` | $50.0 \le \rho \le 120.0$ | $\text{kN/m}^3$ |

---

## 3. Concrete Deck Slab Material Properties

### Standard Presets
- Available presets: `M30`, `M35`, `M40`, `M45`, `M50`, `M55`, `M60`, `Custom`.
- Standard values comply with IRC:112–2019 / IRC:22–2015.

### Custom Concrete Parameter Limits

| Parameter Name | Canonical Key | Data Type | Default (M35) | Permissible Range | Unit |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Compressive Strength ($f_{ck}$)** | `material.deck.fck` | `float` | `35.0` | $20.0 \le f_{ck} \le 100.0$ | $\text{MPa}$ |
| **Tensile Strength ($f_{ctm}$)** | `material.deck.fctm` | `float` | `3.2` | $1.5 \le f_{ctm} \le 8.0$ | $\text{MPa}$ |
| **Secant Modulus ($E_{cm}$)** | `material.deck.ecm` | `float` | `31.0` | $10.0 \le E_{cm} \le 60.0$ | $\text{GPa}$ |
| **Weight Density ($\rho_c$)** | `material.deck.density` | `float` | `25.0` | $15.0 \le \rho_c \le 40.0$ | $\text{kN/m}^3$ |
| **Thermal Expansion ($\alpha_c$)**| `material.deck.thermal` | `float` | `1.0e-5` | $5.0\times 10^{-6} \le \alpha_c \le 2.0\times 10^{-5}$ | $/\text{^\circ C}$ |

---

## 4. Transverse Superstructure & Additional Parameters

| Parameter Name | Canonical Key | Default Value | Recommended Bounds | Unit |
| :--- | :--- | :---: | :---: | :---: |
| **Number of Girders** | `superstructure.no_of_girders` | `4` | $2 \le N_g \le 12$ | count |
| **Girder Spacing** | `superstructure.girder_spacing` | `2.5` | $1.5 \le S_g \le 4.5$ | $\text{m}$ |
| **Deck Overhang** | `superstructure.deck_overhang` | `1.25` | $0.5 \le S_o \le 2.5$ | $\text{m}$ |
| **Deck Thickness** | `superstructure.deck_thickness`| `250.0` | $180.0 \le t_{deck} \le 450.0$ | $\text{mm}$ |
| **Crash Barrier Width** | `superstructure.barrier_width` | `0.5` | $0.3 \le W_{cb} \le 1.0$ | $\text{m}$ |
| **Crash Barrier Height**| `superstructure.barrier_height`| `1.0` | $0.8 \le H_{cb} \le 1.5$ | $\text{m}$ |
| **Wearing Coat Thickness**| `superstructure.wearing_coat` | `75.0` | $50.0 \le t_{wc} \le 125.0$ | $\text{mm}$ |

---

## 5. Environmental & Live Loading Parameters (IRC:6–2017)

| Parameter Name | Canonical Key | Default Value | Permissible Range | Unit |
| :--- | :--- | :---: | :---: | :---: |
| **Footpath Pressure** | `load.live_load.footpath_pressure_value` | `4.0` | $2.0 \le p_{fp} \le 6.0$ | $\text{kN/m}^2$ |
| **Live Load Eccentricity** | `load.live_load.eccentricity` | `0.3` | $0.0 \le e \le 1.5$ | $\text{m}$ |
| **Wind Gust Factor** | `load.wind.gust_factor_value` | `1.2` | $1.0 \le G_w \le 2.5$ | — |
| **Wind Drag Coefficient** | `load.wind.drag_coeff_value` | `1.5` | $0.8 \le C_d \le 3.0$ | — |
| **Wind Lift Coefficient** | `load.wind.lift_coeff_value` | `0.75` | $0.2 \le C_L \le 1.5$ | — |
| **Seismic Zone Factor ($Z$)**| `load.seismic.zone_factor` | `0.24` (Zone IV) | $\{0.10, 0.16, 0.24, 0.36\}$ | — |
| **Importance Factor ($I$)** | `load.seismic.importance_factor` | `1.2` | $1.0 \le I \le 1.5$ | — |
| **Response Reduction ($R$)**| `load.seismic.response_reduction` | `3.0` | $2.5 \le R \le 5.0$ | — |

---

## 6. Limit State Partial Safety Factors (IRC:24 / IRC:6)

| Factor Name | Canonical Key | Standard Value | Description |
| :--- | :--- | :---: | :--- |
| **$\gamma_{m0}$** | `design.gamma_m0` | `1.10` | Resistance against yielding (structural steel) |
| **$\gamma_{m1}$** | `design.gamma_m1` | `1.25` | Resistance against ultimate tensile rupture |
| **$\gamma_{v}$** | `design.gamma_v` | `1.25` | Shear connector resistance factor |
| **$\gamma_{s}$** | `design.gamma_s` | `1.15` | Reinforcing steel resistance factor |
| **$\gamma_{c}$** | `design.gamma_c` | `1.50` | Concrete limit state basic safety factor |

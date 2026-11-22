# Expected Results & Verification Baselines Directory

This directory contains benchmark data, theoretical calculation hand-sheets, and literature baselines against which OsdagBridge analysis and design outputs are verified.

## Reference Baselines Catalog

1. **IRC:24 Example Problem**: Standard design of a 24m plate girder composite bridge.
   - Governing Mid-Span Bending Moment: $M_{u,approx} \approx \frac{w L^2}{8} + M_{live,max}$
   - Web depth to span ratio: $d_w \approx L / 12$ to $L / 15$
   - Allowable live load deflection: $\delta_{all} = L / 800 = 30.0\text{ mm}$ for $24.0\text{ m}$ span.

2. **Grillage Discretization Verification**:
   - Comparison of longitudinal load distribution factors calculated via `ospgrillage` against Courbon's method and Guyon-Massonnet grillage theory.

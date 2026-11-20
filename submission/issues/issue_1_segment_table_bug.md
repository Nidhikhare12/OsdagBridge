## Girder segment tables (G2 to G8) don't update when you change span and re-run

So I was testing something pretty basic — running the design twice without closing the app. First run was with span = 20 m, everything default (8 girders, E 350A, M40 deck). After it finished I unlocked the design, changed the span to 24 m and skew to 15°, then clicked Design again.

The 3D model looked correct — 24 m span. Output dock gave results. Seemed fine.

But then I opened the saved `.osi` file (it's just YAML) and something looked off:

```
member_properties.girder_details.segment_table.G1: [{id: G1M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G2: [{id: G2M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G3: [{id: G3M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G4: [{id: G4M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G5: [{id: G5M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G6: [{id: G6M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G7: [{id: G7M1, start: 0.0, end: 20.0}]
member_properties.girder_details.segment_table.G8: [{id: G8M1, start: 0.0, end: 20.0}]
```

Every single girder is still showing `end: 20.0`. The span was 24 m at the time of design. The `geometry.span` key in the same file correctly shows `24`, but the segment tables were never updated.

I double-checked by parsing both files with a small script:

```python
import yaml

for name in ['TC01_Baseline_18m.osi', 'TC02_Consecutive_24m.osi']:
    with open(name) as f:
        d = yaml.safe_load(f)
    for i in range(1, 9):
        seg = d.get(f'member_properties.girder_details.segment_table.G{i}')
        print(name, f'G{i}  end =', seg[0]['end'])
```

Output:
```
TC01_Baseline_18m.osi G1  end = 20.0
TC01_Baseline_18m.osi G2  end = 20.0
...
TC02_Consecutive_24m.osi G1  end = 20.0
TC02_Consecutive_24m.osi G2  end = 20.0
TC02_Consecutive_24m.osi G3  end = 20.0
...
TC02_Consecutive_24m.osi G8  end = 20.0
```

All 20.0. None of them got updated to 24.0.

---

**Where I think this is happening:**

I looked at `defaults.py` around the section that builds the segment tables. It looks like the code for G2 onwards reads whatever is already in `input_dict` from the previous run and just reuses it — it doesn't recalculate from the current span value. G1 might get handled separately or first and also ends up stale.

Something like this is probably the issue:

```python
# for G2, G3... it's reading the old dict entry and copying it back unchanged
existing = input_dict.get(segment_key_for_girder)
if existing:
    input_dict[segment_key_for_girder] = existing  # this is a no-op, stale data stays
```

The fix I'd suggest is to always regenerate segment tables from the current span value when the design function runs, not read from the previous dict:

```python
span = float(input_dict.get(KEY_SPAN, 20.0))
for g in all_girders:
    input_dict[segment_key(g)] = [{'id': f'{g}M1', 'start': 0.0, 'end': span}]
```

---

**Why it's a problem:**

The segment table is what tells the analysis engine where along the girder length to extract forces and design stiffeners. If G2–G8 internally think they're 20 m but the bridge is actually 24 m, the member force extraction and DCR calculations for those girders are going to be wrong — even though the 3D view looks fine. It's the kind of bug that's easy to miss visually.

---

**Steps to reproduce:**

1. Launch OsdagBridge
2. Set span = 20 m, 8 girders, E 350A, M40, no skew → click Design → save as `run1.osi`
3. Unlock → change span to 24 m, skew to 15° → click Design → save as `run2.osi`
4. Open `run2.osi` and check `member_properties.girder_details.segment_table.G2` through `G8`
5. All will show `end: 20.0`

**Branch:** dev (commit d74f56d)  
**Python:** 3.12, osdagbridge-env  
**OS:** Windows 11

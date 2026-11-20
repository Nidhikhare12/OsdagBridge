## Cross-bracing capacity is completely blank in output — "no such table: Material" in console

I noticed something weird after running the design — the Output Dock shows dashes (—) for all the cross-bracing bays. At first I thought maybe cross-bracing capacity just doesn't show up there, but then I looked at the console output and saw this repeating for every single inter-girder pair:

```
[CrossBracing] SKIP G1-G2 diagonal tension: no such table: Material
[CrossBracing] SKIP G2-G3 diagonal tension: no such table: Material
[CrossBracing] SKIP G3-G4 diagonal tension: no such table: Material
[CrossBracing] SKIP G4-G5 diagonal tension: no such table: Material
[CrossBracing] SKIP G5-G6 diagonal tension: no such table: Material
[CrossBracing] SKIP G6-G7 diagonal tension: no such table: Material
[CrossBracing] SKIP G7-G8 diagonal tension: no such table: Material
```

This happened on all three of my test runs — E 350A material in TC01 and TC02, and my custom steel grade (`custom_steel_450_570`, fy = 450 MPa) in TC03. So it's not a material-specific thing, it's happening for everything.

---

**What I think is going on:**

The error says `no such table: Material`. I looked at the SQLite database (`Intg_osdag.sqlite`) with DB Browser and the table is actually called `Steel_Grade_Properties`, not `Material`. So somewhere in `osdag_core/utils/common/material.py` (probably), there's a query doing:

```sql
SELECT ... FROM Material WHERE grade = 'E 350A' ...
```

That throws `sqlite3.OperationalError: no such table: Material`, and then `crossbracingforces.py` around line 658 catches that exception and just skips the calculation with a log message instead of raising it properly.

So the cross-bracing design silently does nothing. If you weren't reading the console you'd never know.

---

**Two ways to fix this:**

Option 1 — just fix the table name in `material.py`:
```python
# change FROM Material → FROM Steel_Grade_Properties
cursor.execute("SELECT ... FROM Steel_Grade_Properties WHERE ...")
```

Option 2 — add a view to the database so both names work (less code change):
```sql
CREATE VIEW IF NOT EXISTS Material AS SELECT * FROM Steel_Grade_Properties;
```

Also, the `except` block in `crossbracingforces.py` that swallows this error is too broad. At minimum it should log a warning that includes the exception message, not just silently skip. That way if the table name ever gets renamed again, it won't take this long to catch.

---

**To reproduce:**

1. Launch OsdagBridge with any valid input set
2. Keep cross-bracing enabled (it's on by default)
3. Click Design
4. Watch the console — you'll see the SKIP messages for all pairs
5. Check the Output Dock — cross-bracing capacity shows `—` for all bays

**Branch:** dev (commit d74f56d)  
**Python:** 3.12, osdagbridge-env  
**OS:** Windows 11

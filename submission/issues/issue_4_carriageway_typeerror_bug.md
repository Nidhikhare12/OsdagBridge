## Unhandled TypeError in layout solver when carriageway width is not yet set

When opening a project with incomplete geometry inputs or when the layout solver runs before the carriageway width input is populated in the GUI, the application crashes with an unhandled `TypeError`.

```python
TypeError: float() argument must be a string or a real number, not 'NoneType'
```

---

### What is going on:

In `defaults.py` (around line 908), the solver calculates the transverse layout of girders and footpath overhangs by directly casting:

```python
cw = float(basic_input_dict.get(KEY_CARRIAGEWAY_WIDTH))
```

If `KEY_CARRIAGEWAY_WIDTH` is `None` or an empty string `""` (for instance, during initial dialog instantiation or if an imported file has missing geometry keys), `basic_input_dict.get()` returns `None`. Passing `None` to `float()` immediately triggers `TypeError` without providing user-facing validation.

---

### Suggested Fix:

Add safe input validation in `defaults.py` (~line 908):

```python
# In defaults.py (~line 908)
raw_cw = basic_input_dict.get(KEY_CARRIAGEWAY_WIDTH)
if raw_cw is None or str(raw_cw).strip() == "":
    raise ValueError("Carriageway width is required before bridge layout can be computed.")
cw = float(raw_cw)
```

This ensures the user is shown a clear validation prompt rather than the entire GUI crashing with an unhandled exception.

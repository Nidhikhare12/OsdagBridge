"""
results_data.py
---------------
Extracts analysis results from an ospgrillage OspGrillage model directly into
the flat dict format consumed by plot_generator functions.

Accepts the OspGrillage model object and its xarray Dataset directly, with no
bridge-wrapper dependency.
"""

from __future__ import annotations
import json
import math
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path

import openseespy.opensees as ops

from .results_data_post_processing import post_process, FORCE_KEEP, DISP_KEEP


class LazyLoadcaseResults(Mapping):
    """
    Per-loadcase results table backed by the xarray dataset.

    Behaves like ``{loadcase: {id: {component: value}}}`` but materializes a
    load case's nested dict only on access and holds at most ``_MAX_CACHED``
    of them resident. Consumers (the governing-force scans, dumps, dialogs)
    walk load cases sequentially, so the small LRU yields one materialization
    per case instead of keeping every case's tree of Python floats alive —
    previously ~n_loadcases full nested dicts duplicating the dataset.

    The FORCE_KEEP/DISP_KEEP component whitelist (post_process's cleaning
    step) is applied during materialization, so entries look exactly like the
    cleaned eager dicts.
    """
    _MAX_CACHED = 8

    def __init__(self, ds_all, var: str, keep=None):
        self._ds = ds_all
        self._var = var
        self._keep = keep
        self._keys = [str(lc) for lc in ds_all.coords["Loadcase"].values]
        self._key_set = set(self._keys)
        self._cache: OrderedDict = OrderedDict()

    def _materialize(self, lc: str) -> dict:
        da = self._ds[self._var].sel(Loadcase=lc)
        cids = [str(c) for c in da.coords["Component"].values]
        col_idx = (
            list(range(len(cids))) if self._keep is None
            else [i for i, c in enumerate(cids) if c in self._keep]
        )
        kept = [cids[i] for i in col_idx]
        dim = "Element" if "Element" in da.coords else "Node"
        ids = da.coords[dim].values
        return {
            str(int(i)): {c: row[j] for c, j in zip(kept, col_idx)}
            for i, row in zip(ids, da.values.tolist())
        }

    def __getitem__(self, lc):
        lc = str(lc)
        if lc in self._cache:
            self._cache.move_to_end(lc)
            return self._cache[lc]
        if lc not in self._key_set:
            raise KeyError(lc)
        table = self._materialize(lc)
        self._cache[lc] = table
        if len(self._cache) > self._MAX_CACHED:
            self._cache.popitem(last=False)
        return table

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

_TOOLS_DIR = Path(__file__).resolve().parents[5] / "tools"


# =============================================================================
# MEMBER CLASSIFICATION & TRANSVERSE-MEMBER RESULTS
# =============================================================================
# Plot keys (as chosen in the output dock) -> result components in the dataset.
# Forces: (i-end, j-end) element end-force components; displacements: nodal dof.
FORCE_COMPONENT_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}
DISP_COMPONENT_MAP = {"Dx": "x", "Dy": "y", "Dz": "z"}

TRANSVERSE_KIND_END_DIAPHRAGM = "end_diaphragm"
TRANSVERSE_KIND_CROSS_BRACING = "cross_bracing"

_COORD_TOL = 1e-3


def split_longitudinal_transverse(nodes: dict, members: dict, tol: float = _COORD_TOL):
    """
    Split OpenSees element tags into longitudinal and transverse members.

    Longitudinal: both end nodes share the same Y and Z (the element runs along
    the span, global X). Everything else spans across the deck: end diaphragms
    (``start_edge`` / ``end_edge``) and intermediate cross bracings
    (``transverse_slab``). Works for skewed (oblique) meshes because only the
    lateral coordinate is tested, never X.
    """
    longitudinal, transverse = [], []
    for tag, (n1, n2) in members.items():
        if n1 not in nodes or n2 not in nodes:
            continue
        if (abs(nodes[n1][2] - nodes[n2][2]) < tol and
                abs(nodes[n1][1] - nodes[n2][1]) < tol):
            longitudinal.append(tag)
        else:
            transverse.append(tag)
    return longitudinal, transverse


def _main_girder_nodes(nodes: dict, members: dict, longitudinal: list, edge_dist: float) -> set:
    """Nodes lying on main-girder lines (edge-beam lines excluded when an overhang exists)."""
    lines: dict = {}
    for tag in longitudinal:
        n1, n2 = members[tag]
        lines.setdefault(round(nodes[n1][2], 3), set()).update((n1, n2))
    ordered = [lines[z] for z in sorted(lines)]
    if edge_dist > 0 and len(ordered) > 2:
        ordered = ordered[1:-1]          # outermost lines are edge beams, not girders
    return set().union(*ordered) if ordered else set()


def classify_transverse_lines(nodes: dict, members: dict, edge_dist: float = 0.0) -> list[dict]:
    """
    Group transverse elements into lines across the deck.

    Only elements connecting two main-girder nodes are kept: these are the
    diaphragm / cross-bracing elements. Overhang pieces between an edge beam and
    the exterior girder are deck slab cantilevers and are excluded (same rule as
    ``results_data_post_processing.build_crossbracings``).

    Returns lines sorted along the span. The first and last line sit on the
    supports and are end diaphragms; the rest are intermediate cross bracings::

        [{"name": "ED1", "kind": "end_diaphragm", "elements": [...], "nodes": [...]}, ...]

    Elements inside a line are ordered from G1 towards Gn.
    """
    nodes = {int(k): v for k, v in nodes.items()}
    members = {int(k): [int(n) for n in v] for k, v in members.items()}
    longitudinal, transverse = split_longitudinal_transverse(nodes, members)
    girder_nodes = _main_girder_nodes(nodes, members, longitudinal, edge_dist)

    elems = [e for e in transverse if all(n in girder_nodes for n in members[e])]

    # Connected components of the transverse-element graph = one line each
    node_to_elems: dict = {}
    for e in elems:
        for n in members[e]:
            node_to_elems.setdefault(n, []).append(e)
    seen, groups = set(), []
    for e in elems:
        if e in seen:
            continue
        stack, comp = [e], []
        seen.add(e)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for n in members[cur]:
                for nxt in node_to_elems.get(n, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
        groups.append(comp)

    def _mid(e, axis):
        n1, n2 = members[e]
        return 0.5 * (nodes[n1][axis] + nodes[n2][axis])

    lines = []
    for comp in groups:
        comp.sort(key=lambda e: _mid(e, 2))                      # G1 -> Gn
        line_nodes = sorted({n for e in comp for n in members[e]}, key=lambda n: nodes[n][2])
        x_mid = sum(_mid(e, 0) for e in comp) / len(comp)
        lines.append({"elements": comp, "nodes": line_nodes, "x": x_mid})
    lines.sort(key=lambda ln: ln["x"])

    n_cb = 0
    for idx, ln in enumerate(lines):
        if idx == 0 or idx == len(lines) - 1:
            ln["kind"] = TRANSVERSE_KIND_END_DIAPHRAGM
            ln["name"] = "ED1" if idx == 0 else "ED2"
        else:
            n_cb += 1
            ln["kind"] = TRANSVERSE_KIND_CROSS_BRACING
            ln["name"] = f"CB{n_cb}"
    return lines


def _component_lookup(ds, var: str, wanted: str):
    """Case-insensitive component match in ds[var] (ospgrillage names vary)."""
    for c in ds[var].coords["Component"].values:
        if str(c).lower() == wanted.lower():
            return c
    return None


def _local_axes(p_start, p_end):
    """Member axes: e1 along the member, e2 vertical (global Y), e3 = e1 x e2.
    For a girder along +X this is the global frame; for a transverse member it
    gives axial along the member, Vy/My about the vertical, Mz in-plane bending."""
    d = [p_end[k] - p_start[k] for k in range(3)]
    L = math.sqrt(sum(c * c for c in d)) or 1.0
    e1 = [c / L for c in d]
    up = (0.0, 1.0, 0.0)
    e3 = [e1[1] * up[2] - e1[2] * up[1], e1[2] * up[0] - e1[0] * up[2], e1[0] * up[1] - e1[1] * up[0]]
    n3 = math.sqrt(sum(c * c for c in e3)) or 1.0
    e3 = [c / n3 for c in e3]
    e2 = [e3[1] * e1[2] - e3[2] * e1[1], e3[2] * e1[0] - e3[0] * e1[2], e3[0] * e1[1] - e3[1] * e1[0]]
    return e1, e2, e3


_GLOBAL_END_COMPONENTS = ("Vx", "Vy", "Vz", "Mx", "My", "Mz")
# plot key -> (vector: "V" force / "M" moment, local axis index)
_LOCAL_COMPONENT = {"Fx": ("V", 0), "Fy": ("V", 1), "Fz": ("V", 2),
                    "Mx": ("M", 0), "My": ("M", 1), "Mz": ("M", 2)}


def extract_transverse_member_results(ds, nodes: dict, members: dict,
                                      plot_key: str, edge_dist: float = 0.0) -> list[dict]:
    """
    Pull one result component for every transverse line, for a single load case.

    Parameters
    ----------
    ds        : xarray.Dataset already reduced to one load case (``ds_all.sel(Loadcase=lc)``)
    plot_key  : "Fx", "Fy", "Fz", "Mx", "My", "Mz" (Fx, Vy, Vz, Tx, My, Mz in the UI)
                or "Dx", "Dy", "Dz"

    Returns
    -------
    list of lines (see classify_transverse_lines) with an added ``segments`` list::

        {"elem": tag, "nodes": (n1, n2), "x": (x1, x2), "z": (z1, z2), "v": (v1, v2)}

    plus ``max`` / ``min`` over the line.

    Forces (kN, kNm) are reported in each member's own axes, so the labels mean
    the same thing as on the girders: Fx axial, Vy vertical shear, Vz horizontal
    shear, Tx torsion, My bending about the vertical axis, Mz bending in the
    vertical plane. ospgrillage returns element end forces in global axes; for
    a member running across the deck (global Z) the raw global Mx would actually
    be its bending moment, hence the rotation. Members are read from the G1 side
    to the Gn side; the value at the start node is the start-end force and at the
    far node the negated far-end force (same convention as the girder diagrams).
    Displacements (mm) are nodal and stay in global axes, with the same vertical
    sign flip as the girder deflection plot.
    """
    nodes = {int(k): v for k, v in nodes.items()}
    members = {int(k): [int(n) for n in v] for k, v in members.items()}
    lines = classify_transverse_lines(nodes, members, edge_dist)

    is_disp = plot_key in DISP_COMPONENT_MAP
    if is_disp:
        comp = _component_lookup(ds, "displacements", DISP_COMPONENT_MAP[plot_key])
        if comp is None:
            return []
        da = ds["displacements"].sel(Component=comp)
        disp = {int(n): float(v) for n, v in zip(da.coords["Node"].values, da.values)}
        sign = -1.0 if DISP_COMPONENT_MAP[plot_key] in ("y", "z") else 1.0   # same as deflection plot
    else:
        names = [f"{c}_{end}" for end in ("i", "j") for c in _GLOBAL_END_COMPONENTS]
        comps = [_component_lookup(ds, "forces", n) for n in names]
        if any(c is None for c in comps):
            return []
        wanted = [e for ln in lines for e in ln["elements"]]
        sub = ds["forces"].sel(Element=wanted, Component=comps).values
        end_forces = {}
        for e, row in zip(wanted, sub):
            row = [float(v) for v in row]
            end_forces[e] = {"i": {"V": row[0:3], "M": row[3:6]},
                             "j": {"V": row[6:9], "M": row[9:12]}}
        vec_kind, axis = _LOCAL_COMPONENT[plot_key]

    for ln in lines:
        segs = []
        for e in ln["elements"]:
            n1, n2 = members[e]
            ends = ("i", "j")
            # Always run G1 -> Gn so lines read left-to-right on the plot
            if nodes[n1][2] > nodes[n2][2]:
                n1, n2, ends = n2, n1, ("j", "i")
            if is_disp:
                v1 = sign * disp.get(n1, 0.0) * 1000.0
                v2 = sign * disp.get(n2, 0.0) * 1000.0
            else:
                ax_vec = _local_axes(nodes[n1], nodes[n2])[axis]
                f_start = end_forces[e][ends[0]][vec_kind]
                f_end = end_forces[e][ends[1]][vec_kind]
                v1 = sum(a * b for a, b in zip(f_start, ax_vec)) / 1000.0      # N -> kN, N.m -> kNm
                v2 = -sum(a * b for a, b in zip(f_end, ax_vec)) / 1000.0
            segs.append({
                "elem": e, "nodes": (n1, n2),
                "x": (nodes[n1][0], nodes[n2][0]),
                "z": (nodes[n1][2], nodes[n2][2]),
                "v": (round(v1, 4), round(v2, 4)),
            })
        ln["segments"] = segs
        vals = [v for s in segs for v in s["v"]]
        ln["max"] = max(vals) if vals else 0.0
        ln["min"] = min(vals) if vals else 0.0
    return lines


def _build_nodes_members() -> tuple[dict, dict]:
    """Read node coords and element connectivity from the live openseespy model."""
    nodes = {
        int(n): list(map(float, ops.nodeCoord(n)))
        for n in ops.getNodeTags()
    }
    members = {
        int(e): list(map(int, ops.eleNodes(e)))
        for e in ops.getEleTags()
    }
    return nodes, members


def dump_full_data(
    model,
    edge_dist: float = 0.0,
    out_path: str | Path | None = None,
    dataset=None,
) -> dict:
    """
    Dump the *entire* extracted result data to a JSON file.

    Unlike ``restructure_data(model, dev=True)``, this writes the complete,
    un-filtered data dict (including ``groups``, ``reactions``,
    ``forces_shell``, ``stresses_shell`` and ``edge_dist`` — keys that
    ``post_process`` would otherwise drop) and performs **no** other side
    effects (no crossbracing dump, no plotly HTML generation).

    Parameters
    ----------
    model : OspGrillage
        Fully analysed ospgrillage model (analyze() already called).
    edge_dist : float
        Deck overhang distance in metres (0.0 when no overhang).
    out_path : str | Path, optional
        Destination JSON path.  Defaults to ``tools/bridge_full_data.json``.

    Returns
    -------
    dict — the full data dict that was written.
    """
    data = _build_full_data(model, edge_dist, dataset=dataset)

    if out_path is None:
        _TOOLS_DIR.mkdir(exist_ok=True)
        out_path = _TOOLS_DIR / "bridge_full_data.json"
    else:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print("=" * 60)
    print(f"[full data] saved → {out_path.resolve()}")
    print("=" * 60)

    return data


def restructure_data(
    model,
    edge_dist: float = 0.0,
    dev: bool = False,
    dataset=None,
    lazy: bool = False,
) -> dict:
    """
    Restructure xarray analysis results into a flat dict for plot_generator and
    any other consumer.  Optionally dumps to tools/bridge_plot_data.json.

    Uses all available ospgrillage APIs to extract metadata (nodes, groups) 
    and results (forces, displacements, reactions, shell results).

    Parameters
    ----------
    model : OspGrillage
        Fully analysed ospgrillage model (analyze() already called).
    dataset : xarray.Dataset, optional
        Pre-computed results dataset.  When omitted, ``model.get_results()``
        is called to obtain it.
    edge_dist : float
        Deck overhang distance in metres (0.0 when no overhang).
    dev : bool
        If True, also write the result to tools/bridge_plot_data.json.

    Returns
    -------
    dict — structure::

    {
        "nodes": {
            "1": [0.0, 0.0, 0.0],
            "2": [0.0, 0.0, 0.75],
            "...": "..."
        },

        "members": {
            "1": [1, 2],
            "2": [2, 3],
            "...": "..."
        },

        "groups": {
            "edge_beam": [
                11,
                22,
                33,
                "..."
            ],

            "exterior_main_beam_1": [
                12,
                23,
                34,
                "..."
            ],

            "exterior_main_beam_2": [
                22,
                33,
                44,
                "..."
            ],

            "interior_main_beam": [
                13,
                24,
                35,
                "..."
            ],

            "start_edge": [
                1,
                2,
                3,
                "..."
            ],
            "end_edge": [
                138,
                139,
                140,
                141,
                ...
            ],
            "transverse_slab": [
                6,
                7,
                8,
                9,
                ...,

            "shell_slab": []
        },

        "longitudinal_members": [
            11,
            12,
            13,
            "..."
        ],

        "transverse_members": [
            1,
            2,
            3,
            "..."
        ],

        "edge_dist": 0.75,

        "loadcases": [
            "girder self weight",
            "superimposed dead load",
            "live load",
            "..."
        ],

        "force_components": [
            "Mx_i",
            "Mx_j",
            "My_i",
            "My_j",
            "Mz_i",
            "Mz_j",
            "Vx_i",
            "Vx_j",
            "Vy_i",
            "Vy_j",
            "Vz_i",
            "Vz_j"
        ],

        "disp_components": [
            "theta_x",
            "theta_y",
            "theta_z",
            "x",
            "y",
            "z"
        ],

        "forces": {
            "girder self weight": {
            "1": {
                "Mx_i": -0.7137482121047469,
                "Mx_j": -4478.21603280773,
                "My_i": 0.0,
                "My_j": 0.0,
                "...": "..."
            },

            "2": {
                "...": "..."
            },

            "...": "..."
            },

            "live load": {
            "...": "..."
            }
        },

        "displacements": {
            "girder self weight": {
            "1": {
                "theta_x": 2.1983232320953836e-05,
                "theta_y": 0.0,
                "theta_z": 0.00038309565871718596,
                "x": 0.0,
                "y": 1.3989811021922501e-05,
                "z": 0.0
            },

            "2": {
                "...": "..."
            },

            "...": "..."
            }
        },

        "reactions": {
            "girder self weight": {
             "...": "..."
            }
        },

        "forces_shell": {
            "...": "..."
        },

        "stresses_shell": {
            "...": "..."
        }
    }
    """
    data = _build_full_data(model, edge_dist, dataset=dataset, lazy=lazy)

    if dev:
        # dev dumps require eager (JSON-serializable) tables.
        _dump(data, "bridge_plot_data_raw.json")

    data = post_process(data)

    if dev:
        _dump(data)
        _dump_crossbracing(data)
        _plot_dev(model, model.get_results())

    return data


def _build_full_data(model, edge_dist: float = 0.0, dataset=None, lazy: bool = False) -> dict:
    """
    Build the complete, un-filtered result data dict from the live model and
    its xarray results.  This is the shared extraction step used by both
    ``restructure_data`` (before post-processing) and ``dump_full_data``.

    When ``dataset`` is provided it is used in place of ``model.get_results()``.
    This is how the envelope pseudo load cases (``Envelope ULS`` /
    ``Envelope SLS``) reach the dump: they live only on the cached, augmented
    dataset, never on the model's freshly-rebuilt results.
    """
    ds_all = model.get_results() if dataset is None else dataset
    # Deduplicate: ospgrillage appends results on every analyze() call, so
    # a second analyze() (e.g. after adding the governing LL case) produces
    # duplicate Loadcase entries.  Keep first occurrence of each name and
    # drop the duplicates from ds_all so that .sel(Loadcase=lc) always
    # returns a 0-d slice (not a multi-row array that breaks float()).
    _seen_lcs: set = set()
    _unique_idx: list = []
    for _i, _lc in enumerate(ds_all.coords["Loadcase"].values):
        _s = str(_lc)
        if _s not in _seen_lcs:
            _seen_lcs.add(_s)
            _unique_idx.append(_i)
    if len(_unique_idx) < len(ds_all.coords["Loadcase"].values):
        ds_all = ds_all.isel(Loadcase=_unique_idx)
    loadcases = [str(lc) for lc in ds_all.coords["Loadcase"].values]

    # ── 1. Metadata from live model / ospgrillage APIs ────────────────
    nodes, members = _build_nodes_members()

    # Extract standard member groups via ospgrillage get_element API
    standard_groups = [
        "edge_beam", "exterior_main_beam_1", "exterior_main_beam_2",
        "interior_main_beam", "start_edge", "end_edge", "transverse_slab",
        "shell_slab"
    ]
    groups = {}
    for group_name in standard_groups:
        try:
            # get_element returns list of tags
            groups[group_name] = [int(e) for e in model.get_element(
                member=group_name, options="elements")]
        except Exception:
            groups[group_name] = []

    # Coordinate components
    ds0 = ds_all.isel(Loadcase=0)
    force_components = [str(
        c) for c in ds0["forces"].coords["Component"].values] if "forces" in ds0.data_vars else []
    disp_components = [str(
        c) for c in ds0["displacements"].coords["Component"].values] if "displacements" in ds0.data_vars else []

    # Classify members: longitudinal = both nodes share same Z and same Y
    longitudinal_members, transverse_members = split_longitudinal_transverse(nodes, members)

    data: dict = {
        "nodes": {str(k): list(v) for k, v in nodes.items()},
        "members": {str(k): list(v) for k, v in members.items()},
        "groups": groups,
        "longitudinal_members": longitudinal_members,
        "transverse_members": transverse_members,
        "edge_dist": float(edge_dist),
        "loadcases": list(loadcases),
        "force_components": force_components,
        "disp_components": disp_components,
        "forces": {},
        "displacements": {},
        "reactions": {},
        "forces_shell": {},
        "stresses_shell": {},
    }

    # Lazy mode: the two big per-loadcase tables are served straight from the
    # dataset on demand (LRU of a few load cases) instead of being duplicated
    # up front as nested dicts of Python floats. The minor tables (reactions /
    # shell results) stay eager below.
    if lazy:
        if "forces" in ds_all.data_vars:
            data["forces"] = LazyLoadcaseResults(ds_all, "forces", FORCE_KEEP)
        if "displacements" in ds_all.data_vars:
            data["displacements"] = LazyLoadcaseResults(ds_all, "displacements", DISP_KEEP)

    # ── 2. Results from xarray Dataset ────────────────────────────────
    # Extract full numpy arrays once per load case instead of one .sel()
    # call per (element/node × component) — avoids tens of thousands of
    # individual xarray label lookups.
    for lc in loadcases:
        ds = ds_all.sel(Loadcase=lc)
        str_lc = str(lc)

        # Displacements — one .values call → (n_nodes, n_comps) numpy array
        if not lazy and "displacements" in ds.data_vars:
            arr  = ds["displacements"].values
            nids = ds["displacements"].coords["Node"].values
            cids = [str(c) for c in ds["displacements"].coords["Component"].values]
            data["displacements"][str_lc] = {
                str(int(n)): dict(zip(cids, row.tolist()))
                for n, row in zip(nids, arr)
            }

        # Forces — one .values call → (n_elems, n_comps) numpy array
        if not lazy and "forces" in ds.data_vars:
            arr  = ds["forces"].values
            eids = ds["forces"].coords["Element"].values
            cids = [str(c) for c in ds["forces"].coords["Component"].values]
            data["forces"][str_lc] = {
                str(int(e)): dict(zip(cids, row.tolist()))
                for e, row in zip(eids, arr)
            }

        # Reactions — one .values call → (n_nodes, n_comps) numpy array
        if "reactions" in ds.data_vars:
            arr  = ds["reactions"].values
            nids = ds["reactions"].coords["Node"].values
            cids = [str(c) for c in ds["reactions"].coords["Component"].values]
            data["reactions"][str_lc] = {
                str(int(n)): dict(zip(cids, row.tolist()))
                for n, row in zip(nids, arr)
            }

        # Shell Forces — one .values call → (n_elems, n_comps) numpy array
        if "forces_shell" in ds.data_vars:
            arr  = ds["forces_shell"].values
            eids = ds["forces_shell"].coords["Element"].values
            cids = [str(c) for c in ds["forces_shell"].coords["Component"].values]
            data["forces_shell"][str_lc] = {
                str(int(e)): dict(zip(cids, row.tolist()))
                for e, row in zip(eids, arr)
            }

        # Shell Stresses — one .values call → (n_elems, n_stress_comps) numpy array
        if "stresses_shell" in ds.data_vars:
            arr  = ds["stresses_shell"].values
            eids = ds["stresses_shell"].coords["Element"].values
            cids = [str(c) for c in ds["stresses_shell"].coords["Stress"].values]
            data["stresses_shell"][str_lc] = {
                str(int(e)): dict(zip(cids, row.tolist()))
                for e, row in zip(eids, arr)
            }

    return data


def _dump_crossbracing(data: dict) -> None:
    """Write raw crossbracing Vz forces to tools/crossbracing_results.json."""
    import math
    import warnings as _warnings

    EQ_TOL = 1e-3  # kN

    cb_chains  = data.get("crossbracings", [])
    forces     = data.get("forces", {})
    load_cases = data.get("loadcases", list(forces.keys()))

    results = {}

    for cb_num, chain in enumerate(cb_chains, start=1):
        mems = chain.get("members", [])
        if not mems:
            continue

        m_id = str(mems[0])

        start = chain.get("start")
        end   = chain.get("end")
        length_m = None
        if start and end:
            sc = start["coords"]
            ec = end["coords"]
            length_m = round(math.sqrt(sum((ec[i] - sc[i]) ** 2 for i in range(3))), 4)

        lc_results = []

        for lc in load_cases:
            lc_str = str(lc)
            elem_f = forces.get(lc_str, {}).get(m_id, {})

            vz_i = elem_f.get("Vz_i")
            vz_j = elem_f.get("Vz_j")

            if vz_i is None or vz_j is None:
                continue

            vz_i_kn = vz_i / 1e3
            vz_j_kn = vz_j / 1e3

            eq_ok   = abs(vz_i_kn + vz_j_kn) <= EQ_TOL
            warning = None

            if not eq_ok:
                warning = (
                    f"Vz_i={vz_i_kn:.4f} kN, Vz_j={vz_j_kn:.4f} kN — "
                    f"expected Vz_i = -Vz_j (diff={vz_i_kn + vz_j_kn:.4f} kN)"
                )
                _warnings.warn(
                    f"[CB {cb_num}] LC '{lc_str}': equilibrium violated — {warning}",
                    stacklevel=2,
                )

            lc_results.append({
                "load_case":      lc_str,
                "Vz_i_kN":        round(vz_i_kn, 4),
                "Vz_j_kN":        round(vz_j_kn, 4),
                "type":           "tension" if vz_i_kn > 0 else "compression",
                "equilibrium_ok": eq_ok,
                "warning":        warning,
            })

        # Forces are in global axis. Cross-bracings run along global Z, so Vz is their axial force.
        # Vz_i > 0 → tension, Vz_i < 0 → compression.
        tension_rows     = [r for r in lc_results if r["Vz_i_kN"] >  0]
        compression_rows = [r for r in lc_results if r["Vz_i_kN"] < 0]

        critical_tension = None
        if tension_rows:
            row = max(tension_rows, key=lambda r: r["Vz_i_kN"])  # largest positive = worst tension
            critical_tension = {
                "load_case": row["load_case"],
                "Vz_i_kN":  row["Vz_i_kN"],
                "Vz_j_kN":  row["Vz_j_kN"],
            }

        critical_compression = None
        if compression_rows:
            row = min(compression_rows, key=lambda r: r["Vz_i_kN"])  # most negative = worst compression
            critical_compression = {
                "load_case": row["load_case"],
                "Vz_i_kN":  row["Vz_i_kN"],
                "Vz_j_kN":  row["Vz_j_kN"],
            }

        left_girder  = chain.get("left_girder", "")
        right_girder = chain.get("right_girder", "")
        girder_pair  = f"{left_girder}-{right_girder}" if left_girder and right_girder else None

        results[str(cb_num)] = {
            "cb_number":            cb_num,
            "member_id":            m_id,
            "girder_pair":          girder_pair,
            "length_m":             length_m,
            "critical_tension":     critical_tension,
            "critical_compression": critical_compression,
            "results":              lc_results,
        }

    _TOOLS_DIR.mkdir(exist_ok=True)
    out_path = _TOOLS_DIR / "crossbracing_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("=" * 60)
    print(f"[crossbracing] saved → {out_path.resolve()}")
    print("=" * 60)


def _extract_osdag_summary(result: dict) -> dict:
    if not result:
        return {}
    def _first(*keys):
        for k in keys:
            v = result.get(k)
            if v is not None:
                return v
        return None

    return {
        "section":     _first("section_size.designation", "Optimum.Designation"),
        "capacity_kN": _first("Member.tension_capacity",  "Design.Strength"),
        "efficiency":  _first("Member.efficiency",        "Optimum.UR"),
        "slenderness": result.get("Member.Slenderness"),
        "connection":  "Welded" if "Weld.Type" in result else "Bolted",
    }


def enrich_crossbracing_dump(pair_designs: dict) -> None:
    """
    Update tools/crossbracing_results.json with Osdag design results.

    Parameters
    ----------
    pair_designs : dict
        {
            "G1-G2": {
                "diagonal": {"tension": result_or_None, "compression": result_or_None},
                "chord":    {"tension": result_or_None, "compression": result_or_None},
            }, ...
        }
    """
    out_path = _TOOLS_DIR / "crossbracing_results.json"
    if not out_path.exists():
        return

    with open(out_path) as f:
        data = json.load(f)

    for entry in data.values():
        pair    = entry.get("girder_pair")
        designs = pair_designs.get(pair, {})

        diag_designs  = designs.get("diagonal", {})
        chord_designs = designs.get("chord",    {})

        if entry.get("critical_tension"):
            entry["critical_tension"]["osdag_diagonal"] = _extract_osdag_summary(
                diag_designs.get("tension") or {}
            )
            entry["critical_tension"]["osdag_chord"] = _extract_osdag_summary(
                chord_designs.get("tension") or {}
            )

        if entry.get("critical_compression"):
            entry["critical_compression"]["osdag_diagonal"] = _extract_osdag_summary(
                diag_designs.get("compression") or {}
            )
            entry["critical_compression"]["osdag_chord"] = _extract_osdag_summary(
                chord_designs.get("compression") or {}
            )

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print("=" * 60)
    print(f"[crossbracing] enriched with Osdag designs → {out_path.resolve()}")
    print("=" * 60)


def build_load_effects_cache(result_handler) -> dict:
    """
    Pre-compute per-girder, per-load-case max/min Mz and Vy for all non-vehicle
    load cases.  Called once at the end of design() and stored on the bridge as
    ``_load_effects_cache``.

    Structure returned::

        {
            "G1": {
                "SW":      {"Mz_max": 123.4, "Mz_min": -45.6, "Vy_max": 78.9, "Vy_min": -12.3},
                "BASIC_1": {"Mz_max": ..., ...},
                ...
            },
            "G2": { ... },
        }

    Values are in kNm (Mz) and kN (Vy).
    Vehicle static / moving load cases are excluded so the table only shows
    dead loads and combination load cases.  Any load case whose name contains
    "moving" is also excluded.
    """
    ds = result_handler.ds
    if ds is None:
        return {}

    g_map, _ = result_handler.build_girders(verbose=False)
    classified = result_handler.classify_loadcases()

    exclude = set(
        classified.get("vehicle_static", []) +
        classified.get("vehicle_moving", [])
    )
    lcs = [
        lc for lc in classified.get("all", [])
        if lc not in exclude and "moving" not in str(lc).lower()
    ]

    cache: dict = {}
    gi = 1
    for girder, gdata in g_map.items():
        if girder.startswith("EB"):
            continue
        girder_label = f"G{gi}"
        gi += 1
        elements = gdata["elements"]
        cache[girder_label] = {}
        for lc in lcs:
            mz_vals: list[float] = []
            vy_vals: list[float] = []
            for comp in ("Mz_i", "Mz_j"):
                for eid in elements:
                    try:
                        val = float(ds.sel(Loadcase=lc, Element=eid, Component=comp)["forces"]) / 1000.0
                        mz_vals.append(val)
                    except Exception:
                        pass
            for comp in ("Vy_i", "Vy_j"):
                for eid in elements:
                    try:
                        val = float(ds.sel(Loadcase=lc, Element=eid, Component=comp)["forces"]) / 1000.0
                        vy_vals.append(val)
                    except Exception:
                        pass
            if mz_vals or vy_vals:
                cache[girder_label][str(lc)] = {
                    "Mz_max": round(max(mz_vals), 3) if mz_vals else None,
                    "Mz_min": round(min(mz_vals), 3) if mz_vals else None,
                    "Vy_max": round(max(vy_vals), 3) if vy_vals else None,
                    "Vy_min": round(min(vy_vals), 3) if vy_vals else None,
                }
    return cache


def build_deflections_cache(result_handler) -> dict:
    """
    Pre-compute maximum vertical (y) deflection per girder for:
      - live load only  (load case "1.0 LL")
      - total load      (load case "1.0 DL + 1.0 LL")

    Returns::

        {
            "G1": {"live_mm": 12.3, "total_mm": 25.6},
            "G2": {...},
        }

    Values are in mm (converted from metres, which is OpenSees' native unit).
    Edge-beam girders (EB1/EB2) are skipped; remaining girders are numbered G1…Gn.
    """
    ds = result_handler.ds
    if ds is None:
        return {}
    disp_da = ds.get("displacements")
    if disp_da is None:
        return {}

    all_lcs = [str(lc) for lc in ds.coords["Loadcase"].values]

    # Governing LL case created by create_governing_ll_load_case(partial_safety_factor=1.0)
    ll_case = next(
        (lc for lc in all_lcs if lc.strip() == "1.0 LL"),
        None,
    )
    # DL + LL combination created by create_dl_ll_combination(dl_factor=1.0, ll_factor=1.0)
    dl_ll_case = next(
        (lc for lc in all_lcs if " DL + " in lc and lc.strip().endswith("LL")
         and not lc.startswith(("BASIC_", "SLS_", "SEISMIC_", "ACCIDENTAL_"))),
        None,
    )

    g_map, _ = result_handler.build_girders(verbose=False)
    node_set = set(disp_da.coords["Node"].values)

    def _max_defl_mm(lc_name: str | None, nodes: list) -> float | None:
        if lc_name is None or not nodes:
            return None
        try:
            vals = []
            for node in nodes:
                if node not in node_set:
                    continue
                v = float(disp_da.sel(Loadcase=lc_name, Node=node, Component="y")) * 1000.0
                vals.append(v)
            return round(max(abs(v) for v in vals), 3) if vals else None
        except Exception:
            return None

    cache: dict = {}
    gi = 1
    for girder, gdata in g_map.items():
        if girder.startswith("EB"):
            continue
        girder_label = f"G{gi}"
        gi += 1
        nodes = gdata.get("path", [])
        cache[girder_label] = {
            "live_mm":  _max_defl_mm(ll_case,    nodes),
            "total_mm": _max_defl_mm(dl_ll_case, nodes),
        }

    return cache

def build_forces_summary(result_handler, load_effects_cache: dict) -> dict:
    """
    Build Chapter 4 Table 4.1 data by reusing load_effects_cache for Mz/Vy
    values and fetching only x-locations and reactions from the dataset.

    Called once from compute_load_effects_cache() immediately after
    build_load_effects_cache() so the cache is already available.

    Parameters
    ----------
    result_handler   : PlateGirderAnalysisResults
    load_effects_cache : dict — output of build_load_effects_cache()
        Structure: {girder_label: {lc_name: {Mz_max, Mz_min, Vy_max, Vy_min}}}

    Returns
    -------
    dict with two keys:
        "load_cases" : {lc_name: {max_bm, bm_girder, bm_location,
                                   max_sf, sf_girder, sf_location}}
        "reactions"  : {lc_name: {left_kN, right_kN}}
    """
    ds = result_handler.ds
    if ds is None or not load_effects_cache:
        return {"load_cases": {}, "reactions": {}}

    # Build girder map and node coords once — reused for both location and reactions
    g_map, _ = result_handler.build_girders(verbose=False)
    nodes_coords, _, _ = result_handler.build_grillage_connectivity()

    # Map cache labels (G1, G2, …) → g_map keys (which may be EB1/G2/G3/EB2 when edge_dist > 0)
    # Mirrors the exact skip-and-recount logic in build_load_effects_cache
    cache_label_to_gmap_key = {}
    gi = 1
    for girder_name in g_map:
        if girder_name.startswith("EB"):
            continue
        cache_label_to_gmap_key[f"G{gi}"] = girder_name
        gi += 1

    # Collect the same filtered load case list the cache was built with
    all_lcs = set()
    for girder_data in load_effects_cache.values():
        all_lcs.update(girder_data.keys())

    lc_summary = {}
    rxn_summary = {}

    for lc in all_lcs:
        # ── 1. Derive max_bm / bm_girder and max_sf / sf_girder from cache ──
        global_bm, bm_girder = 0.0, "—"
        global_sf, sf_girder = 0.0, "—"

        for girder_label, lc_data in load_effects_cache.items():
            entry = lc_data.get(lc)
            if not entry:
                continue

            # correct — check both max and min, take whichever has larger magnitude
            mz_max = entry.get("Mz_max")
            mz_min = entry.get("Mz_min")
            mz = mz_max if (mz_max is not None and abs(mz_max) >= abs(mz_min or 0.0)) else mz_min

            vy_max = entry.get("Vy_max")
            vy_min = entry.get("Vy_min")
            vy = vy_max if (vy_max is not None and abs(vy_max) >= abs(vy_min or 0.0)) else vy_min

            if mz is not None and abs(mz) > abs(global_bm):
                global_bm = mz
                bm_girder = girder_label
            if vy is not None and abs(vy) > abs(global_sf):
                global_sf = vy
                sf_girder = girder_label

        # ── 2. Fetch x-location for the winning girder's max Mz and max Vy ──
        bm_location = None
        sf_location = None

        bm_gmap_key = cache_label_to_gmap_key.get(bm_girder)
        sf_gmap_key = cache_label_to_gmap_key.get(sf_girder)

        if bm_gmap_key:
            best_abs = 0.0
            for eid, n1, n2 in g_map[bm_gmap_key].get("element_map", []):
                for comp, node in (("Mz_i", n1), ("Mz_j", n2)):
                    try:
                        val = float(ds.sel(
                            Loadcase=lc, Element=eid, Component=comp
                        )["forces"]) / 1000.0
                        if abs(val) > best_abs:
                            best_abs = abs(val)
                            bm_location = round(nodes_coords[node][0], 3)
                    except Exception:
                        pass

        if sf_gmap_key:
            best_abs = 0.0
            for eid, n1, n2 in g_map[sf_gmap_key].get("element_map", []):
                for comp, node in (("Vy_i", n1), ("Vy_j", n2)):
                    try:
                        val = float(ds.sel(
                            Loadcase=lc, Element=eid, Component=comp
                        )["forces"]) / 1000.0
                        if abs(val) > best_abs:
                            best_abs = abs(val)
                            sf_location = round(nodes_coords[node][0], 3)
                    except Exception:
                        pass

        lc_summary[lc] = {
            "max_bm":      round(global_bm, 3),
            "bm_girder":   bm_girder,
            "bm_location": bm_location,
            "max_sf":      round(global_sf, 3),
            "sf_girder":   sf_girder,
            "sf_location": sf_location,
        }

        # ── 3. Reactions — sum Ra and Rb across all interior girders ──
        left_total  = 0.0
        right_total = 0.0

        for gmap_key in cache_label_to_gmap_key.values():
            element_map = g_map[gmap_key].get("element_map", [])
            if not element_map:
                continue
            eid_start, n1_start, _ = element_map[0]
            eid_end,   _,  n2_end  = element_map[-1]
            try:
                ra = float(ds.sel(
                    Loadcase=lc, Element=eid_start, Component="Vy_i"
                )["forces"]) / 1000.0
                rb = -float(ds.sel(
                    Loadcase=lc, Element=eid_end, Component="Vy_j"
                )["forces"]) / 1000.0
                left_total  += ra
                right_total += rb
            except Exception:
                pass

        rxn_summary[lc] = {
            "left_kN":  round(left_total,  3),
            "right_kN": round(right_total, 3),
        }

    return {"load_cases": lc_summary, "reactions": rxn_summary}


def _dump(data: dict, filename: str = "bridge_plot_data.json") -> None:
    """Write data to tools/<filename>."""
    _TOOLS_DIR.mkdir(exist_ok=True)
    out_path = _TOOLS_DIR / filename
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print("=" * 60)
    print(f"[plot data] saved → {out_path.resolve()}")
    print("=" * 60)


def _plot_dev(model, ds_all) -> None:
    """
    Generate interactive plotly HTML files in tools/plots/ using the
    ospgrillage plotting API.  Called only when dev=True.

    Files produced
    --------------
    model.html  — 3-D mesh with node/element labels
    Mz.html     — Bending moment diagram      (plot_bmd,   all members)
    Fy.html     — Shear force diagram         (plot_sfd,   all members)
    Mx.html     — Torsion moment diagram      (plot_tmd,   all members)
    y.html      — Vertical deflection         (plot_def,   all members)
    Fx.html     — Axial force                 (plot_force, all members)
    Fz.html     — Transverse shear            (plot_force, all members)
    My.html     — Minor-axis bending moment   (plot_force, all members)
    """
    import ospgrillage as og

    plots_dir = _TOOLS_DIR / "plots"
    plots_dir.mkdir(exist_ok=True)

    # ── 1. Model visualisation ────────────────────────────────────────────
    try:
        fig = og.plot_model(
            model,
            backend="plotly",
            show_node_labels=True,
            show_element_labels=True,
            show=False,
        )
        out = plots_dir / "model.html"
        fig.write_html(str(out))
        print(f"[dev plot] model.html → {out}")
    except Exception as exc:
        print(f"[dev plot] model failed: {exc}")

    # ── 2. Convenience wrappers (Mz, Fy, Mx, y) ──────────────────────────
    convenience = [
        ("Mz.html", og.plot_bmd),
        ("Fy.html", og.plot_sfd),
        ("Mx.html", og.plot_tmd),
        ("y.html",  og.plot_def),
    ]
    for fname, fn in convenience:
        try:
            fig = fn(model, ds_all, backend="plotly", show=False)
            out = plots_dir / fname
            fig.write_html(str(out))
            print(f"[dev plot] {fname} → {out}")
        except Exception as exc:
            print(f"[dev plot] {fname} failed: {exc}")

    # ── 3. Generic plot_force for remaining components ────────────────────
    generic = ["Vx", "Vz", "My"]
    for comp in generic:
        fname = f"{comp}.html"
        try:
            fig = og.plot_force(
                model, ds_all,
                member=og.Members.ALL,
                component=comp,
                show=False,
            )
            out = plots_dir / fname
            fig.write_html(str(out))
            print(f"[dev plot] {fname} → {out}")
        except Exception as exc:
            print(f"[dev plot] {fname} failed: {exc}")

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
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path

import numpy as np

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

    # Classify members (longitudinal = both nodes share the same Z and Y).
    # Transverse elements are split by role using the ospgrillage groups:
    # end diaphragms (support lines), intermediate cross-bracings, and the
    # deck-overhang strips that only connect an edge beam to a girder.
    member_map = classify_grillage_members(nodes, members, edge_dist=edge_dist, groups=groups)

    data: dict = {
        "nodes": {str(k): list(v) for k, v in nodes.items()},
        "members": {str(k): list(v) for k, v in members.items()},
        "groups": groups,
        "longitudinal_members": member_map["longitudinal"],
        "transverse_members": member_map["end_diaphragms"] + member_map["cross_bracings"],
        "end_diaphragm_members": member_map["end_diaphragms"],
        "cross_bracing_members": member_map["cross_bracings"],
        "deck_transverse_members": member_map["deck_transverse"],
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


# =============================================================================
# TRANSVERSE MEMBER MAPPING (end diaphragms + intermediate cross-bracings)
# =============================================================================

# ospgrillage member groups assigned in analyser.create_model()
OSP_GROUP_START_EDGE      = "start_edge"        # end diaphragm at x = 0
OSP_GROUP_END_EDGE        = "end_edge"          # end diaphragm at x = L
OSP_GROUP_TRANSVERSE_SLAB = "transverse_slab"   # intermediate transverse members

TRANSVERSE_KIND_END_DIAPHRAGM = "end_diaphragm"
TRANSVERSE_KIND_CROSS_BRACING = "cross_bracing"

_COORD_TOL = 1e-3   # m


def _as_int_maps(nodes: dict, members: dict) -> tuple[dict, dict]:
    """Accept str- or int-keyed nodes/members (live model or JSON dump)."""
    n = {int(k): [float(c) for c in v] for k, v in nodes.items()}
    m = {int(k): (int(v[0]), int(v[1])) for k, v in members.items()}
    return n, m


def classify_grillage_members(nodes: dict, members: dict, edge_dist: float = 0.0,
                              groups: dict | None = None) -> dict:
    """
    Split grillage element tags by structural role.

    Longitudinal elements have both end nodes on the same line (equal Y and Z).
    Every other element is transverse and is further classified:

    * a transverse element is *structural* (diaphragm / bracing) only if it
      connects two **different main girders**; elements touching an edge beam
      (deck overhang strips) are ``deck_transverse``;
    * structural elements in the ospgrillage ``start_edge`` / ``end_edge``
      groups are end diaphragms, the rest are intermediate cross-bracings.
      Without groups (e.g. a JSON dump) the support lines are recognised
      geometrically: both nodes are the first / last node of their girder.

    Returns
    -------
    dict with int tag lists ``longitudinal``, ``end_diaphragms``,
    ``cross_bracings``, ``deck_transverse`` and ``girder_of_node``
    ({node: "G<i>"}) for the main girders.
    """
    nodes, members = _as_int_maps(nodes, members)

    longitudinal, transverse = [], []
    lines: dict = {}
    for tag, (n1, n2) in members.items():
        if n1 not in nodes or n2 not in nodes:
            continue
        (x1, y1, z1), (x2, y2, z2) = nodes[n1][:3], nodes[n2][:3]
        if abs(z1 - z2) < _COORD_TOL and abs(y1 - y2) < _COORD_TOL:
            longitudinal.append(tag)
            lines.setdefault(round(z1, 3), []).append(tag)
        else:
            transverse.append(tag)

    # Main girder lines: with an overhang the two outermost lines are edge beams.
    line_zs = sorted(lines)
    girder_zs = line_zs[1:-1] if (edge_dist and edge_dist > 0 and len(line_zs) > 2) else line_zs

    girder_of_node: dict = {}
    line_end_nodes: set = set()
    for idx, z in enumerate(girder_zs, start=1):
        line_nodes = {n for e in lines[z] for n in members[e]}
        for n in line_nodes:
            girder_of_node[n] = f"G{idx}"
        xs = sorted(line_nodes, key=lambda n: nodes[n][0])
        line_end_nodes.update((xs[0], xs[-1]))

    groups = groups or {}
    end_group = {int(e) for e in (groups.get(OSP_GROUP_START_EDGE) or [])}
    end_group |= {int(e) for e in (groups.get(OSP_GROUP_END_EDGE) or [])}

    end_diaphragms, cross_bracings, deck_transverse = [], [], []
    for tag in transverse:
        n1, n2 = members[tag]
        g1, g2 = girder_of_node.get(n1), girder_of_node.get(n2)
        if g1 is None or g2 is None or g1 == g2:
            deck_transverse.append(tag)
            continue
        if end_group:
            is_end = tag in end_group
        else:
            is_end = n1 in line_end_nodes and n2 in line_end_nodes
        (end_diaphragms if is_end else cross_bracings).append(tag)

    return {
        "longitudinal": longitudinal,
        "end_diaphragms": end_diaphragms,
        "cross_bracings": cross_bracings,
        "deck_transverse": deck_transverse,
        "girder_of_node": girder_of_node,
    }


def get_transverse_member_groups(model) -> dict:
    """ospgrillage groups needed to classify transverse members ({group: [tags]})."""
    groups = {}
    for name in (OSP_GROUP_START_EDGE, OSP_GROUP_END_EDGE, OSP_GROUP_TRANSVERSE_SLAB):
        try:
            groups[name] = [int(e) for e in model.get_element(member=name, options="elements")]
        except Exception:
            groups[name] = []
    return groups


def build_transverse_lines(nodes: dict, members: dict, edge_dist: float = 0.0,
                           groups: dict | None = None) -> list[dict]:
    """
    Group the structural transverse elements into transverse lines across the
    deck (one per end diaphragm / cross-bracing position), ordered along the
    span. Elements of one line share nodes, so lines are the connected
    components of the transverse element graph - this also holds for skewed
    (oblique-mesh) decks where a line is not at a single X.

    Returns ``[{"name", "kind", "x", "elements": [tag, ...]}, ...]`` with the
    elements of each line ordered across the width, names ``ED1``/``ED2`` for
    end diaphragms and ``CB1..CBn`` for intermediate cross-bracings.
    """
    member_map = classify_grillage_members(nodes, members, edge_dist, groups)
    nodes_i, members_i = _as_int_maps(nodes, members)

    def _components(tags):
        parent = {}

        def find(a):
            while parent.setdefault(a, a) != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for t in tags:
            n1, n2 = members_i[t]
            parent[find(n1)] = find(n2)
        comps: dict = {}
        for t in tags:
            comps.setdefault(find(members_i[t][0]), []).append(t)
        return list(comps.values())

    def _mid(t, axis):
        n1, n2 = members_i[t]
        return 0.5 * (nodes_i[n1][axis] + nodes_i[n2][axis])

    lines = []
    for kind, tags in ((TRANSVERSE_KIND_END_DIAPHRAGM, member_map["end_diaphragms"]),
                       (TRANSVERSE_KIND_CROSS_BRACING, member_map["cross_bracings"])):
        for comp in _components(tags):
            comp.sort(key=lambda t: _mid(t, 2))                 # across the width
            x = sum(_mid(t, 0) for t in comp) / len(comp)
            lines.append({"kind": kind, "x": x, "elements": comp})

    lines.sort(key=lambda ln: ln["x"])
    counters = {TRANSVERSE_KIND_END_DIAPHRAGM: 0, TRANSVERSE_KIND_CROSS_BRACING: 0}
    prefixes = {TRANSVERSE_KIND_END_DIAPHRAGM: "ED", TRANSVERSE_KIND_CROSS_BRACING: "CB"}
    for ln in lines:
        counters[ln["kind"]] += 1
        ln["name"] = f"{prefixes[ln['kind']]}{counters[ln['kind']]}"
    return lines


def _match_component(available, wanted: str):
    for c in available:
        if str(c).lower() == wanted.lower():
            return c
    return None


def member_local_axes(start, end) -> np.ndarray:
    """
    Unit vectors (rows) of a frame member's local axes, OpenSees-style:
    x from ``start`` to ``end``, y the global vertical (Y) made orthogonal to
    x, z = x × y. For a girder along +X this is the global frame itself.
    """
    p0 = np.asarray(start, dtype=float)[:3]
    p1 = np.asarray(end, dtype=float)[:3]
    ex = p1 - p0
    length = np.linalg.norm(ex)
    if length == 0.0:
        raise ValueError("Zero-length member")
    ex /= length
    up = np.array([0.0, 1.0, 0.0])
    if abs(ex @ up) > 0.999:                     # vertical member: fall back to global X
        up = np.array([1.0, 0.0, 0.0])
    ey = up - (up @ ex) * ex
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    return np.vstack([ex, ey, ez])


def extract_transverse_results(ds, result_key: str, nodes: dict, members: dict,
                               edge_dist: float = 0.0, groups: dict | None = None,
                               loadcase: str | None = None) -> list[dict]:
    """
    Internal forces / displacements of every transverse line for one load case.

    Parameters
    ----------
    ds : xarray.Dataset
        Results of a single load case, or the full dataset plus ``loadcase``.
    result_key : str
        Force key "Fx", "Fy", "Fz", "Mx", "My", "Mz" (kN / kNm) or
        displacement key "Dx", "Dy", "Dz" (mm).

    Returns
    -------
    ``build_transverse_lines`` entries, each extended with ``segments``:
    ``[{"element", "nodes": (n_i, n_j), "points": [(x, z), (x, z)],
    "values": (v_i, v_j)}]`` and the line's ``max`` / ``min`` value.

    Forces are rotated from the global axes ospgrillage reports into each
    member's local axes (``member_local_axes``: x along the member, y
    vertical), so the keys mean the same as on the girder plots - Fx axial,
    Fy/Fz shear, Mx torsion, My/Mz bending (Mz about the horizontal axis,
    i.e. the bending caused by vertical load). Each segment runs in the
    direction of increasing Z and its values are (f_start, -f_end), the same
    end-force convention as the girder SFD/BMD. Vertical / lateral
    displacements are reported positive downward (sag), like the girder
    deflection plot.
    """
    from .plot_generator import FORCE_MAP, DISP_MAP

    if loadcase is not None and "Loadcase" in getattr(ds, "dims", {}):
        ds = ds.sel(Loadcase=loadcase)

    nodes_i, members_i = _as_int_maps(nodes, members)
    lines = build_transverse_lines(nodes, members, edge_dist, groups)
    if not lines:
        return []

    if result_key in FORCE_MAP:
        # ospgrillage reports element end forces in GLOBAL axes. Rotate them
        # into each member's own (local) frame so Fx / Vy / Vz / Tx / My / Mz
        # mean the same thing as on the girder plots: x along the member,
        # y vertical, z = x × y (for a girder along +X this is the identity).
        da = ds["forces"]
        comps = [str(c) for c in da.coords["Component"].values]
        kind = "M" if result_key.startswith("M") else "V"
        axis = "xyz".index(result_key[1].lower())
        wanted = [f"{kind}{a}_{end}" for end in ("i", "j") for a in "xyz"]
        resolved = [_match_component(comps, w) for w in wanted]
        if any(c is None for c in resolved):
            missing = [w for w, c in zip(wanted, resolved) if c is None]
            raise KeyError(f"Force components {missing} not in results")
        tags = [t for ln in lines for t in ln["elements"]]
        avail = {int(e) for e in da.coords["Element"].values}
        tags = [t for t in tags if t in avail]
        sub = np.asarray(da.sel(Element=tags, Component=resolved).values, dtype=float)
        global_end = {t: (row[:3], row[3:]) for t, row in zip(tags, sub)}   # (at node i, at node j)

        def _seg_values(t, n1, n2):
            # n1 -> n2 is the plotting direction (increasing Z), which may be
            # opposite to the element's own i -> j definition.
            if t not in global_end:
                return 0.0, 0.0
            f_i, f_j = global_end[t]
            ni, _ = members_i[t]
            f_start, f_end = (f_i, f_j) if n1 == ni else (f_j, f_i)
            e_local = member_local_axes(nodes_i[n1], nodes_i[n2])[axis]
            # (f_start, -f_end): the same end-force convention as the girder SFD/BMD.
            return (float(f_start @ e_local) / 1000.0 + 0.0,       # N -> kN; +0.0 drops -0.0
                    -float(f_end @ e_local) / 1000.0 + 0.0)

    elif result_key in DISP_MAP:
        da = ds["displacements"]
        comps = [str(c) for c in da.coords["Component"].values]
        target = DISP_MAP[result_key].lstrip("dD")            # "dy" -> "y"
        comp = _match_component(comps, target)
        if comp is None:
            raise KeyError(f"Displacement component {target} not in results")
        sign = -1.0 if comp.lower() in ("y", "z") else 1.0     # positive = sag
        node_ids = sorted({n for ln in lines for t in ln["elements"] for n in members_i[t]})
        avail = {int(n) for n in da.coords["Node"].values}
        node_ids = [n for n in node_ids if n in avail]
        vals = da.sel(Node=node_ids, Component=comp).values
        disp = {n: sign * float(v) * 1000.0 + 0.0 for n, v in zip(node_ids, vals)}  # m -> mm

        def _seg_values(t, n1, n2):
            return disp.get(n1, 0.0), disp.get(n2, 0.0)
    else:
        raise KeyError(f"Unknown result key: {result_key}")

    for ln in lines:
        segments = []
        for t in ln["elements"]:
            n1, n2 = members_i[t]
            # Orient every segment across the width (increasing Z).
            if nodes_i[n1][2] > nodes_i[n2][2]:
                n1, n2 = n2, n1
            v1, v2 = _seg_values(t, n1, n2)
            segments.append({
                "element": t,
                "nodes": (n1, n2),
                "points": [(nodes_i[n1][0], nodes_i[n1][2]), (nodes_i[n2][0], nodes_i[n2][2])],
                "values": (v1, v2),
            })
        values = [v for seg in segments for v in seg["values"]]
        ln["segments"] = segments
        ln["max"] = max(values) if values else 0.0
        ln["min"] = min(values) if values else 0.0
    return lines


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

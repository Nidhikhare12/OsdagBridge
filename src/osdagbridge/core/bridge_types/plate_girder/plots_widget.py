import numpy as np
import plotly.graph_objects as go
import openseespy.opensees as ops

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}

# ============================================================
# UNIFIED SCENE & CAMERA CONFIGURATION
# ============================================================
def make_shared_scene(show_grid=True):
    """Return scene config with optional grid visibility."""
    grid_color = "rgba(150, 150, 150, 0.2)" if show_grid else "rgba(0,0,0,0)"
    return dict(
        camera=dict(
            up=dict(x=0, y=1, z=0),
            center=dict(x=0, y=0, z=0),
            # eye=dict(x=0, y=0.1, z=2.5)         //changesssss
            eye=dict(x=1.2, y=0.8, z=1.8)
        ),
        xaxis=dict(
            title=dict(text="<b>Span Length</b>", font=dict(size=12, color="black")),
            showbackground=False,
            showgrid=show_grid,
            gridcolor=grid_color,
            zeroline=False, showline=True, linecolor="black", linewidth=2,
            ticks="outside", tickfont=dict(size=11, color="black"),
            visible=True, showspikes=False
        ),
        zaxis=dict(
            title=dict(text="<b>Bridge Width</b>", font=dict(size=12, color="black")),
            showbackground=False,
            showgrid=show_grid,
            gridcolor=grid_color,
            zeroline=False, showline=True, linecolor="black", linewidth=2,
            ticks="outside", tickfont=dict(size=11, color="black"),
            autorange="reversed", visible=True, showspikes=False
        ),
        yaxis=dict(
            showbackground=False, showgrid=False, zeroline=False,
            visible=False, showspikes=False
        ),
        aspectmode='data',
    )

# Default scene (grid on)
SHARED_SCENE = make_shared_scene(show_grid=True)


def build_nodes_members():
    """Build nodes and members dicts from the active openseespy model."""
    nodes = {
        int(n): list(map(float, ops.nodeCoord(n)))
        for n in ops.getNodeTags()
    }
    members = {
        int(e): list(map(int, ops.eleNodes(e)))
        for e in ops.getEleTags()
    }
    return nodes, members


def add_grillage_background(fig, nodes_dict, members_dict):
    x_grill, y_grill, z_grill = [], [], []
    for ele_tag, (n1, n2) in members_dict.items():
        x1, _, z1 = nodes_dict[n1]
        x2, _, z2 = nodes_dict[n2]
        x_grill.extend([x1, x2, None])
        y_grill.extend([0, 0, None])
        z_grill.extend([z1, z2, None])

    fig.add_trace(go.Scatter3d(
        x=x_grill, y=y_grill, z=z_grill, mode='lines',
        line=dict(color='darkgrey', width=2), opacity=0.9,
        hoverinfo='skip', showlegend=False
    ))


def add_coordinate_triad(fig, nodes, scale=0.10):
    xs = [coord[0] for coord in nodes.values()]
    ys = [coord[1] for coord in nodes.values()]
    zs = [coord[2] for coord in nodes.values()]

    span_x = max(xs) - min(xs)
    span_z = max(zs) - min(zs)
    span = max(span_x, span_z)
    if span == 0:
        span = 5000

    L = span * scale
    ox, oy, oz = min(xs), min(ys), min(zs)

    cad_colors = {'X': '#FF4136', 'Y': '#2ECC40', 'Z': '#0074D9'}

    def draw_axis(axis_name, end_pt, vec, color):
        fig.add_trace(go.Scatter3d(
            x=[ox, end_pt[0]], y=[oy, end_pt[1]], z=[oz, end_pt[2]],
            mode='lines', line=dict(color=color, width=5),
            hoverinfo='skip', showlegend=False
        ))
        fig.add_trace(go.Cone(
            x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]],
            u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=L * 0.2, anchor="tail",
            showscale=False, hoverinfo='skip',
            colorscale=[[0, color], [1, color]]
        ))

    draw_axis('X', [ox + L, oy, oz], [L, 0, 0], cad_colors['X'])
    draw_axis('Y', [ox, oy + L, oz], [0, L, 0], cad_colors['Y'])
    draw_axis('Z', [ox, oy, oz + L], [0, 0, L], cad_colors['Z'])

    fig.add_trace(go.Scatter3d(
        x=[ox + L * 1.2, ox, ox], y=[oy, oy + L * 1.2, oy], z=[oz, oz, oz + L * 1.2],
        mode='text', text=['<b>X</b>', '<b>Y</b>', '<b>Z</b>'],
        textfont=dict(
            color=[cad_colors['X'], cad_colors['Y'], cad_colors['Z']],
            size=13, family="Arial Black, sans-serif"
        ),
        hoverinfo='skip', showlegend=False
    ))


# ============================================================
# HELPER: get sorted girders from model
# ============================================================
def _get_sorted_girders(nodes, members):
    """Return list of (z_val, elem_list) sorted by z, for longitudinal girders only."""
    from collections import defaultdict

    Z_TOL = 3
    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    girders = defaultdict(list)
    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    return sorted(girders.items(), key=lambda item: item[0])


def _build_polyline(elems, comp_i, comp_j, nodes, members, ds):
    """Build xs, ys, zs, vals, node_ids arrays for a girder."""
    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    xs, ys, zs, vals, node_ids = [], [], [], [], []
    for e in elems:
        n1, n2 = members[e]
        x1, y1, z1 = nodes[n1]
        xs.append(x1); ys.append(y1); zs.append(z1)
        vals.append(round(get_force(e, comp_i), 3))
        node_ids.append(n1)

    last_e = elems[-1]
    n1, n2 = members[last_e]
    x2, y2, z2 = nodes[n2]
    xs.append(x2); ys.append(y2); zs.append(z2)
    vals.append(round(get_force(last_e, comp_j), 3))
    node_ids.append(n2)
    return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids


def _find_component(ds, name):
    for c in ds["Component"].values:
        if c.lower() == name.lower():
            return c
    return None


# ============================================================
# SFD  (with optional contour + scale + isolate + grid toggle)
# ============================================================
def build_figure_sfd(ds, force_key, nodes, members,
                     show_contour=False, scale_factor=1.0,
                     isolate_girder=None, show_grid=True):
    """
    Build Shear Force Diagram figure.

    Parameters
    ----------
    ds              : xarray dataset for the selected loadcase
    force_key       : one of FORCE_MAP keys  (e.g. "Fy")
    nodes / members : dicts from build_nodes_members()
    show_contour    : bool  – colour the SFD surface with a Jet colormap
    scale_factor    : float – multiplier on the Y displacement of the diagram
    isolate_girder  : int or None – 1-based girder index to show alone (None = all)
    show_grid       : bool  – toggle axis grid lines
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = _find_component(ds, comp_i_name)
    comp_j = _find_component(ds, comp_j_name)

    sorted_girders = _get_sorted_girders(nodes, members)

    # Gather global force range for contour colour normalisation
    all_vals = []
    for _, elems in sorted_girders:
        _, _, _, vy, _ = _build_polyline(elems, comp_i, comp_j, nodes, members, ds)
        all_vals.extend(vy.tolist())
    v_min, v_max = (min(all_vals), max(all_vals)) if all_vals else (0, 1)

    fig_sfd = go.Figure()
    add_grillage_background(fig_sfd, nodes, members)
    add_coordinate_triad(fig_sfd, nodes)

    girder_trace_indices = {}   # girder_name -> list of trace indices for legend toggle

    for i, (z_val, elems) in enumerate(sorted_girders):
        girder_name = f"G{i + 1}"

        # Isolate: skip girders that are not selected
        if isolate_girder is not None and (i + 1) != isolate_girder:
            continue

        xs, ys, zs, Vy_raw, node_ids = _build_polyline(
            elems, comp_i, comp_j, nodes, members, ds
        )
        Vy = Vy_raw.astype(float)
        z_base = np.mean(zs)

        # Compute scale
        span = max(xs) - min(xs)
        val_range = max(Vy) - min(Vy)
        if val_range == 0:
            base_scale = 1.0 if max(Vy) == 0 else 0.25 * abs(span / max(Vy))
        else:
            base_scale = 0.25 * abs(span / val_range)

        shear_scale = base_scale * scale_factor

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        start_idx = len(fig_sfd.data)
        girder_trace_indices[girder_name] = []

        # ── Surface ──────────────────────────────────────────────────────
        if show_contour:
            surface_colors = [Vy_step, Vy_step]
            colorscale = "Jet"
            cmin, cmax = v_min, v_max
        else:
            surface_colors = [[1] * len(y_step), [1] * len(y_step)]
            colorscale = [[0, 'blue'], [1, 'blue']]
            cmin, cmax = None, None

        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step],
            y=[np.zeros(len(y_step)), y_step],
            z=[z_step, z_step],
            surfacecolor=surface_colors,
            colorscale=colorscale,
            cmin=cmin, cmax=cmax,
            opacity=0.25 if show_contour else 0.2,
            showscale=show_contour,
            colorbar=dict(title=force_key, thickness=12, len=0.6) if show_contour else None,
            hoverinfo="skip",
            name=girder_name,
            legendgroup=girder_name,
            showlegend=False,
        ))
        girder_trace_indices[girder_name].append(len(fig_sfd.data) - 1)

        # ── Base line ────────────────────────────────────────────────────
        fig_sfd.add_trace(go.Scatter3d(
            x=list(xs) + [None], y=[0] * len(xs) + [None], z=list(zs) + [None],
            mode="lines", line=dict(color="green", width=3),
            hoverinfo="skip", showlegend=False,
            name=girder_name, legendgroup=girder_name,
        ))
        girder_trace_indices[girder_name].append(len(fig_sfd.data) - 1)

        # ── Shear line ───────────────────────────────────────────────────
        hover_text = [
            f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
            for x, v, nid in zip(
                x_step, Vy_step,
                np.repeat(node_ids, 2)[1:-1]
            )
        ]
        line_color = "blue"
        fig_sfd.add_trace(go.Scatter3d(
            x=list(x_step) + [None],
            y=list(y_step) + [None],
            z=list(z_step) + [None],
            mode="lines", line=dict(color=line_color, width=6),
            hoverinfo="text", text=hover_text + [None],
            name=girder_name, legendgroup=girder_name,
            showlegend=True,  # show in legend for toggle
        ))
        girder_trace_indices[girder_name].append(len(fig_sfd.data) - 1)

        # ── Cliff lines ──────────────────────────────────────────────────
        cliff_x, cliff_y, cliff_z = [], [], []
        for xi, vyi in zip(xs, Vy):
            cliff_x.extend([xi, xi, None])
            cliff_z.extend([z_base, z_base, None])
            cliff_y.extend([0, -vyi * shear_scale if xi == xs[-1] else vyi * shear_scale, None])

        fig_sfd.add_trace(go.Scatter3d(
            x=cliff_x, y=cliff_y, z=cliff_z, mode="lines",
            line=dict(color="blue", width=4),
            hoverinfo="skip", showlegend=False,
            name=girder_name, legendgroup=girder_name,
        ))
        girder_trace_indices[girder_name].append(len(fig_sfd.data) - 1)

        # ── Label ────────────────────────────────────────────────────────
        fig_sfd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text",
            text=[girder_name], textposition="middle left",
            textfont=dict(size=11, color="black"),
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name,
        ))
        girder_trace_indices[girder_name].append(len(fig_sfd.data) - 1)

    fig_sfd.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(
            bgcolor="#E6F2FF", font_size=12,
            font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1
        ),
        scene=make_shared_scene(show_grid=show_grid),
     
        legend=dict(
        title=dict(text="Girders"),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.6)",
        bordercolor="#cccccc",
        borderwidth=1,
        font=dict(size=10),
),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig_sfd.to_json()


# ============================================================
# BMD
# ============================================================
def build_figure_bmd(ds, force_key, nodes, members,
                     scale_factor=1.0, isolate_girder=None, show_grid=True):
    """
    Build Bending Moment Diagram figure.

    Extra params vs original:
        scale_factor    : float – multiplier on Y displacement
        isolate_girder  : int or None – 1-based girder index
        show_grid       : bool
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = _find_component(ds, comp_i_name)
    comp_j = _find_component(ds, comp_j_name)

    sorted_girders = _get_sorted_girders(nodes, members)

    fig_bmd = go.Figure()
    add_grillage_background(fig_bmd, nodes, members)
    add_coordinate_triad(fig_bmd, nodes)

    master_max_x, master_max_y, master_max_z = [], [], []
    master_min_x, master_min_y, master_min_z = [], [], []
    summary_data = {}

    for i, (gid, elems) in enumerate(sorted_girders):
        girder_name = f"G{i + 1}"

        if isolate_girder is not None and (i + 1) != isolate_girder:
            continue

        xs, ys, zs, mz, node_ids = _build_polyline(
            elems, comp_i, comp_j, nodes, members, ds
        )
        span = max(xs) - min(xs)
        val_range = max(mz) - min(mz)
        if val_range == 0:
            base_scale = 1.0 if max(mz) == 0 else 0.1 * abs(span / max(mz))
        else:
            base_scale = 0.1 * abs(span / val_range)

        factormz = base_scale * scale_factor
        y_plot = mz * factormz

        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1] * len(xs), [1] * len(xs)],
            colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False,
        ))

        hover_text = [
            f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}"
            for nid, x, v, z in zip(node_ids, xs, mz, zs)
        ]
        fig_bmd.add_trace(go.Scatter3d(
            x=list(xs) + [None], y=list(y_plot) + [None], z=list(zs) + [None],
            mode='lines', line=dict(color="red", width=4),
            showlegend=True, text=hover_text + [None], hoverinfo="text",
            name=girder_name, legendgroup=girder_name,
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1], None], y=[0, 0, None], z=[zs[0], zs[0], None],
            mode='lines', line=dict(color="green", width=3),
            showlegend=False, hoverinfo='skip',
            name=girder_name, legendgroup=girder_name,
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"),
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name,
        ))

        idx_max, max_val = int(np.argmax(mz)), float(max(mz))
        master_max_x.extend([xs[idx_max], xs[idx_max], None])
        master_max_y.extend([0, max_val * factormz, None])
        master_max_z.extend([zs[0], zs[0], None])

        idx_min, min_val = int(np.argmin(mz)), float(min(mz))
        master_min_x.extend([xs[idx_min], xs[idx_min], None])
        master_min_y.extend([0, min_val * factormz, None])
        master_min_z.extend([zs[0], zs[0], None])

        summary_data[girder_name] = {"max": max_val, "min": min_val}

    # HUD
    hud_text = "<b>Extreme Values (N mm)</b><br>" + "-" * 44 + "<br>"
    hud_text += (
        f"<b>{'Girder'.ljust(6).replace(' ','&nbsp;')}</b> | "
        f"<span style='color:#FF4136;'><b>{'Max'.rjust(14).replace(' ','&nbsp;')}</b></span> | "
        f"<span style='color:#0074D9;'><b>{'Min'.rjust(14).replace(' ','&nbsp;')}</b></span><br>"
        + "-" * 44 + "<br>"
    )
    for girder, vals in summary_data.items():
        g_str  = girder.ljust(6).replace(" ", "&nbsp;")
        mx_str = f"{vals['max']:.2f}".rjust(14).replace(" ", "&nbsp;")
        mn_str = f"{vals['min']:.2f}".rjust(14).replace(" ", "&nbsp;")
        hud_text += f"<b>{g_str}</b> | {mx_str} | {mn_str}<br>"

    fig_bmd.add_trace(go.Scatter3d(
        x=master_max_x, y=master_max_y, z=master_max_z,
        mode="lines", line=dict(color="black", width=3),
        legendgroup="max_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_min_x, y=master_min_y, z=master_min_z,
        mode="lines", line=dict(color="black", width=3),
        legendgroup="min_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))

    fig_bmd.update_layout(
        uirevision="constant_view",
        annotations=[dict(
            x=0.02, y=0.98, xref="paper", yref="paper",
            text=hud_text, showarrow=False,
            bgcolor="rgba(33,37,43,0.85)", bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1, borderpad=12,
            font=dict(family="Consolas,'Courier New',monospace", size=12, color="white"),
            align="left", visible=False
        )],
        hoverlabel=dict(
            bgcolor="#FFE4E1", font_size=12,
            font_color="#2C3E50", bordercolor="#CBD5E1", namelength=-1
        ),
        
        legend=dict(
        title=dict(text="Girders"),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.6)",
        bordercolor="#cccccc",
        borderwidth=1,
        font=dict(size=10),
        ),
        scene=make_shared_scene(show_grid=show_grid),
        paper_bgcolor="white", plot_bgcolor="white",
        # margin=dict(l=0, r=0, t=40, b=0),  //changesss
        margin=dict(l=5, r=5, t=30, b=5),
    )
    return fig_bmd.to_json(), summary_data


# ============================================================
# BMD CONTOUR
# ============================================================
def build_figure_bmd_contour(ds, force_key, nodes, members,
                              scale_factor=1.0, isolate_girder=None, show_grid=True):
    """BMD with Jet colour contour. Same extra params as build_figure_bmd."""
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = _find_component(ds, comp_i_name)
    comp_j = _find_component(ds, comp_j_name)

    sorted_girders = _get_sorted_girders(nodes, members)

    # Global range for colour normalisation
    all_mz = []
    for _, elems in sorted_girders:
        _, _, _, mz, _ = _build_polyline(elems, comp_i, comp_j, nodes, members, ds)
        all_mz.extend(mz.tolist())
    v_min, v_max = (min(all_mz), max(all_mz)) if all_mz else (0, 1)

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    master_drop_x, master_drop_y, master_drop_z = [], [], []
    master_drop_color, master_drop_text = [], []
    master_base_x, master_base_y, master_base_z = [], [], []

    for i, (gid, elems) in enumerate(sorted_girders):
        girder_name = f"G{i + 1}"

        if isolate_girder is not None and (i + 1) != isolate_girder:
            continue

        xs, ys, zs, mz, node_ids = _build_polyline(
            elems, comp_i, comp_j, nodes, members, ds
        )
        span = max(xs) - min(xs)
        val_range = max(mz) - min(mz)
        if val_range == 0:
            base_scale = 1.0 if max(mz) == 0 else 0.1 * abs(span / max(mz))
        else:
            base_scale = 0.1 * abs(span / val_range)

        moment_scale = base_scale * scale_factor
        y_plot = mz * moment_scale

        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet",
            cmin=v_min, cmax=v_max,
            opacity=0.4, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False,
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=v_min, cmax=v_max),
            marker=dict(size=12, opacity=0),
            showlegend=True,
            text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}"
                  for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text",
            name=girder_name, legendgroup=girder_name,
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text",
            text=[f"<b>{girder_name}</b>"],
            textposition="middle left", textfont=dict(size=14, color="black"),
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name,
        ))

        master_base_x.extend([xs[0], xs[-1], None])
        master_base_y.extend([0, 0, None])
        master_base_z.extend([zs[0], zs[0], None])

        for xi, zi, mzi, nid in zip(xs, zs, mz, node_ids):
            master_drop_x.extend([xi, xi, None])
            master_drop_y.extend([0, mzi * moment_scale, None])
            master_drop_z.extend([zi, zi, None])
            master_drop_color.extend([mzi, mzi, mzi])
            htext = f"Node {nid}<br>X={xi:.2f}<br>{force_key}={mzi:.2f}"
            master_drop_text.extend([htext, htext, None])

    fig.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode="lines",
        line=dict(color="green", width=3), hoverinfo="skip", showlegend=False
    ))
    if master_drop_x:
        fig.add_trace(go.Scatter3d(
            x=master_drop_x, y=master_drop_y, z=master_drop_z,
            mode="lines+markers",
            line=dict(width=4, color=master_drop_color,
                      colorscale="Jet", cmin=v_min, cmax=v_max),
            marker=dict(size=12, opacity=0),
            showlegend=False, text=master_drop_text, hoverinfo="text"
        ))

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(
            bgcolor="rgba(15,23,42,0.95)", font_size=12,
            font_color="#F8F9FA", bordercolor="#0EA5E9", namelength=-1
        ),
        
        legend=dict(
        title=dict(text="Girders"),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.6)",
        bordercolor="#cccccc",
        borderwidth=1,
        font=dict(size=10),
        ),

        scene=make_shared_scene(show_grid=show_grid),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig.to_json()
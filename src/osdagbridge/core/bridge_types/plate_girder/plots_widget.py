import numpy as np
import plotly.graph_objects as go
import openseespy.opensees as ops
from copy import deepcopy

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}


def _finite_float(value, fallback=0.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return fallback
    return value if np.isfinite(value) else fallback


def _finite_array(values, fallback=0.0):
    return np.nan_to_num(
        np.asarray(values, dtype=float),
        nan=fallback,
        posinf=fallback,
        neginf=fallback,
    )

# ============================================================
# UNIFIED SCENE & CAMERA CONFIGURATION
# ============================================================
# Used by all 3 plots so the camera never jumps when switching dropdowns
SHARED_SCENE = dict(
    camera=dict(
        up=dict(x=0, y=1, z=0),
        center=dict(x=0, y=0, z=0),
        eye=dict(x=0, y=0.1, z=2.5) # Perfect front elevation
    ),
    xaxis=dict(
        title=dict(text="<b>Span Length</b>", font=dict(size=12, color="black")),
        showbackground=False, showgrid=True, gridcolor="rgba(100, 100, 100, 0.15)",
        zeroline=False, showline=True, linecolor="black", linewidth=2,
        ticks="outside", tickfont=dict(size=11, color="black"),
        visible=True, showspikes=False
    ),
    zaxis=dict(
        title=dict(text="<b>Bridge Width</b>", font=dict(size=12, color="black")),
        showbackground=False, showgrid=True, gridcolor="rgba(100, 100, 100, 0.15)",
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
        x1 = _finite_float(x1)
        x2 = _finite_float(x2)
        z1 = _finite_float(z1)
        z2 = _finite_float(z2)
        x_grill.extend([x1, x2, None])
        y_grill.extend([0, 0, None])
        z_grill.extend([z1, z2, None])

    fig.add_trace(go.Scatter3d(
        x=x_grill, y=y_grill, z=z_grill, mode='lines',
        line=dict(color='darkgrey', width=2), opacity=0.9,
        hoverinfo='skip', showlegend=False
    ))

def add_coordinate_triad(fig, nodes, scale=0.10):
    xs = _finite_array([coord[0] for coord in nodes.values()])
    ys = _finite_array([coord[1] for coord in nodes.values()])
    zs = _finite_array([coord[2] for coord in nodes.values()])

    span_x = max(xs) - min(xs)
    span_z = max(zs) - min(zs)
    span = max(span_x, span_z)
    if span == 0: span = 5000

    L = span * scale
    ox, oy, oz = min(xs), min(ys), min(zs)

    cad_colors = {'X': '#FF4136', 'Y': '#2ECC40', 'Z': '#0074D9'}

    def draw_axis(axis_name, end_pt, vec, color):
        fig.add_trace(go.Scatter3d(
            x=[ox, end_pt[0]], y=[oy, end_pt[1]], z=[oz, end_pt[2]],
            mode='lines', line=dict(color=color, width=5), hoverinfo='skip', showlegend=False
        ))
        fig.add_trace(go.Cone(
            x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]], u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=L*0.2, anchor="tail", showscale=False, hoverinfo='skip',
            colorscale=[[0, color], [1, color]]
        ))

    draw_axis('X', [ox + L, oy, oz], [L, 0, 0], cad_colors['X'])
    draw_axis('Y', [ox, oy + L, oz], [0, L, 0], cad_colors['Y'])
    draw_axis('Z', [ox, oy, oz + L], [0, 0, L], cad_colors['Z'])

    fig.add_trace(go.Scatter3d(
        x=[ox + L*1.2, ox, ox], y=[oy, oy + L*1.2, oy], z=[oz, oz, oz + L*1.2],
        mode='text', text=['<b>X</b>', '<b>Y</b>', '<b>Z</b>'],
        textfont=dict(color=[cad_colors['X'], cad_colors['Y'], cad_colors['Z']], size=13, family="Arial Black, sans-serif"),
        hoverinfo='skip', showlegend=False
    ))


def _group_girders(nodes, members):
    Z_TOL = 3
    from collections import defaultdict
    girders = defaultdict(list)

    for ele, conn in members.items():
        try:
            n1, n2 = map(int, conn[:2])
            z1 = round(_finite_float(nodes[n1][2]), Z_TOL)
            z2 = round(_finite_float(nodes[n2][2]), Z_TOL)
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        if z1 == z2:
            girders[z1].append(int(ele))

    if girders:
        return sorted(girders.items(), key=lambda item: item[0])

    node_z = {}
    for n in ops.getNodeTags():
        z = _finite_float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    return sorted(girders.items(), key=lambda item: item[0])


def _selected_girders(sorted_girders, girder_index=None):
    if girder_index is None:
        return sorted_girders

    try:
        index = int(girder_index)
    except (TypeError, ValueError):
        return sorted_girders

    if index < 0 or index >= len(sorted_girders):
        return sorted_girders

    return [sorted_girders[index]]


def _scene_layout(show_grid=True):
    scene = deepcopy(SHARED_SCENE)
    scene["xaxis"]["showgrid"] = show_grid
    scene["zaxis"]["showgrid"] = show_grid
    return scene


def _apply_3d_layout(fig, show_grid=True, margin_top=40):
    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#E6F2FF", font_size=12, font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1),
        scene=_scene_layout(show_grid),
        margin=dict(l=0, r=0, t=margin_top, b=0),
        paper_bgcolor="white", plot_bgcolor="white"
    )


def _apply_contour_layout(fig, show_grid=True):
    fig.update_layout(
        uirevision="constant_view",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=show_grid, zeroline=False, showline=True, linecolor="black"),
        yaxis=dict(showgrid=show_grid, zeroline=False, showline=True, linecolor="black"),
    )


def _build_polyline_for_girder(elem_list, nodes, members, comp_i, comp_j, force_getter):
    xs, ys, zs, vals, node_ids = [], [], [], [], []
    for e in elem_list:
        n1, n2 = members[e]
        x1, y1, z1 = (_finite_float(value) for value in nodes[n1])
        xs.append(x1); ys.append(y1); zs.append(z1)
        vals.append(round(_finite_float(force_getter(e, comp_i)), 3))
        node_ids.append(n1)

    last_e = elem_list[-1]
    n1, n2 = members[last_e]
    x2, y2, z2 = (_finite_float(value) for value in nodes[n2])
    xs.append(x2); ys.append(y2); zs.append(z2)
    vals.append(round(_finite_float(force_getter(last_e, comp_j)), 3))
    node_ids.append(n2)
    return _finite_array(xs), _finite_array(ys), _finite_array(zs), _finite_array(vals), node_ids

# ============================================================
# SFD
# ============================================================
def build_figure_sfd(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, girder_index=None):
    scale_factor = _finite_float(scale_factor, 1.0)

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    girders = _selected_girders(_group_girders(nodes, members), girder_index)
    if not girders:
        return go.Figure().to_json()

    fig_sfd = go.Figure()
    add_grillage_background(fig_sfd, nodes, members)
    add_coordinate_triad(fig_sfd, nodes)

    master_base_x, master_base_y, master_base_z = [], [], []
    master_shear_x, master_shear_y, master_shear_z = [], [], []
    master_hover_text = []
    master_cliff_x, master_cliff_y, master_cliff_z = [], [], []
    master_label_x, master_label_y, master_label_z, master_label_text = [], [], [], []

    for i, (z_val, elems) in enumerate(girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, vy, node_ids = _build_polyline_for_girder(
            elems, nodes, members, comp_i, comp_j, get_force
        )
        Vy = vy.astype(float)
        z_base = np.mean(zs)

        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale * scale_factor
        z_step = [z_base] * len(y_step)

        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[[1]*len(y_step), [1]*len(y_step)], colorscale=[[0, 'blue'], [1, 'blue']],
            opacity=0.2, showscale=False, hoverinfo="skip", name=girder_name,
            legendgroup=girder_name, showlegend=True
        ))

        master_base_x.extend(list(xs) + [None])
        master_base_y.extend([0] * len(xs) + [None])
        master_base_z.extend(list(zs) + [None])

        master_shear_x.extend(list(x_step) + [None])
        master_shear_y.extend(list(y_step) + [None])
        master_shear_z.extend(list(z_step) + [None])

        hover_strings = [f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
                         for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])]
        master_hover_text.extend(hover_strings + [None])

        for xi, vyi in zip(xs, Vy):
            master_cliff_x.extend([xi, xi, None])
            master_cliff_z.extend([z_base, z_base, None])
            master_cliff_y.extend([0, (-vyi if xi == xs[-1] else vyi) * shear_scale * scale_factor, None])

        master_label_x.append(xs[0])
        master_label_y.append(0)
        master_label_z.append(zs[0])
        master_label_text.append(girder_name)

    fig_sfd.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode="lines",
        line=dict(color="green", width=3), hoverinfo="skip", showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_shear_x, y=master_shear_y, z=master_shear_z, mode="lines",
        line=dict(color="blue", width=6), hoverinfo="text", text=master_hover_text, showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_cliff_x, y=master_cliff_y, z=master_cliff_z, mode="lines",
        line=dict(color="blue", width=4), hoverinfo="skip", showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_label_x, y=master_label_y, z=master_label_z, mode="text",
        text=master_label_text, textposition="middle left", textfont=dict(size=11, color="black"),
        showlegend=False, hoverinfo="skip"
    ))

    _apply_3d_layout(fig_sfd, show_grid=show_grid)
    return fig_sfd.to_json()


# ============================================================
# BMD
# ============================================================
def build_figure_bmd(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, girder_index=None):
    scale_factor = _finite_float(scale_factor, 1.0)

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    girders = _selected_girders(_group_girders(nodes, members), girder_index)
    if not girders:
        return go.Figure().to_json(), {}

    fig_bmd = go.Figure()
    add_grillage_background(fig_bmd, nodes, members)
    add_coordinate_triad(fig_bmd, nodes)

    master_line_x, master_line_y, master_line_z = [], [], []
    master_base_x, master_base_y, master_base_z = [], [], []
    master_max_x, master_max_y, master_max_z = [], [], []
    master_min_x, master_min_y, master_min_z = [], [], []
    master_hover_text, master_label_x, master_label_y, master_label_z, master_label_text = [], [], [], [], []

    summary_data = {}

    for i, (gid, elems) in enumerate(girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, mz, node_ids = _build_polyline_for_girder(
            elems, nodes, members, comp_i, comp_j, get_force
        )

        if max(mz) - min(mz) == 0:
            factormz = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * factormz * scale_factor

        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1]*len(xs), [1]*len(xs)], colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip", name=girder_name,
            legendgroup=girder_name, showlegend=True
        ))

        master_line_x.extend(list(xs) + [None])
        master_line_y.extend(list(y_plot) + [None])
        master_line_z.extend(list(zs) + [None])

        hover_text = [f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}" for nid, x, v, z in zip(node_ids, xs, mz, zs)]
        master_hover_text.extend(hover_text + [None])

        master_base_x.extend([xs[0], xs[-1], None])
        master_base_y.extend([0, 0, None])
        master_base_z.extend([zs[0], zs[0], None])

        master_label_x.append(xs[0])
        master_label_y.append(0)
        master_label_z.append(zs[0])
        master_label_text.append(girder_name)

        idx_max, max_val = np.argmax(mz), max(mz)
        master_max_x.extend([xs[idx_max], xs[idx_max], None])
        master_max_y.extend([0, max_val * factormz * scale_factor, None])
        master_max_z.extend([zs[0], zs[0], None])

        idx_min, min_val = np.argmin(mz), min(mz)
        master_min_x.extend([xs[idx_min], xs[idx_min], None])
        master_min_y.extend([0, min_val * factormz * scale_factor, None])
        master_min_z.extend([zs[0], zs[0], None])

        summary_data[girder_name] = {"max": max_val, "min": min_val}

    # =========================================================
    # HUD GENERATOR
    # =========================================================
    hud_text = "<b>Extreme Values (N mm)</b><br>"
    hud_text += "-" * 44 + "<br>"

    h_girder = "Girder".ljust(6).replace(" ", "&nbsp;")
    h_max = "Max".rjust(14).replace(" ", "&nbsp;")
    h_min = "Min".rjust(14).replace(" ", "&nbsp;")

    hud_text += f"<b>{h_girder}</b> | <span style='color: #FF4136;'><b>{h_max}</b></span> | <span style='color: #0074D9;'><b>{h_min}</b></span><br>"
    hud_text += "-" * 44 + "<br>"

    for girder, vals in summary_data.items():
        g_str = girder.ljust(6).replace(" ", "&nbsp;")
        max_str = f"{vals['max']:.2f}".rjust(14).replace(" ", "&nbsp;")
        min_str = f"{vals['min']:.2f}".rjust(14).replace(" ", "&nbsp;")
        hud_text += f"<b>{g_str}</b> | {max_str} | {min_str}<br>"

    fig_bmd.add_trace(go.Scatter3d(
        x=master_line_x, y=master_line_y, z=master_line_z, mode='lines', line=dict(color="red", width=4),
        showlegend=False, text=master_hover_text, hoverinfo="text"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode='lines',
        line=dict(color="green", width=3, dash='solid'), showlegend=False, hoverinfo='skip'
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_label_x, y=master_label_y, z=master_label_z, mode="text", text=master_label_text,
        textposition="middle left", textfont=dict(size=11, color="black"), showlegend=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_max_x, y=master_max_y, z=master_max_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="max_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_min_x, y=master_min_y, z=master_min_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="min_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))

    fig_bmd.update_layout(
        uirevision="constant_view",
        annotations=[
            dict(
                x=0.02, y=0.98, xref="paper", yref="paper", text=hud_text, showarrow=False,
                bgcolor="rgba(33, 37, 43, 0.85)", bordercolor="rgba(255, 255, 255, 0.2)",
                borderwidth=1, borderpad=12,
                font=dict(family="Consolas, 'Courier New', monospace", size=12, color="white"),
                align="left", visible=False
            )
        ],
        hoverlabel=dict(bgcolor="#FFE4E1", font_size=12, font_color="#2C3E50", bordercolor="#CBD5E1", namelength=-1),
        updatemenus=[
            dict(
                type="buttons", direction="right", x=0.5, y=1.15, showactive=True, active=-1,
                buttons=[
                    dict(label="MAX", method="update", args=[{"visible": [True if t.legendgroup == "max_lines" else t.visible for t in fig_bmd.data]}], args2=[{"visible": [False if t.legendgroup == "max_lines" else t.visible for t in fig_bmd.data]}]),
                    dict(label="MIN", method="update", args=[{"visible": [True if t.legendgroup == "min_lines" else t.visible for t in fig_bmd.data]}], args2=[{"visible": [False if t.legendgroup == "min_lines" else t.visible for t in fig_bmd.data]}]),
                    dict(label="SUMMARY", method="relayout", args=[{"annotations[0].visible": True}], args2=[{"annotations[0].visible": False}]),
                ]
            )
        ],
        scene=_scene_layout(show_grid),
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig_bmd.to_json(), summary_data


# ============================================================
# FORCE CONTOUR (Fy / Fx / Fz)
# ============================================================
def build_figure_force_contour(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, girder_index=None):
    scale_factor = _finite_float(scale_factor, 1.0)

    def empty_contour(message):
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)],
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        fig.update_xaxes(title_text="Span Length")
        fig.update_yaxes(title_text="Girder")
        _apply_contour_layout(fig, show_grid=show_grid)
        return fig.to_json()

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)
    if comp_i is None or comp_j is None:
        return empty_contour(f"No {force_key} contour component data")

    def get_force_pair(elem):
        values = []
        for comp in (comp_i, comp_j):
            try:
                value = float(ds["forces"].sel(Element=elem, Component=comp).values)
            except (KeyError, TypeError, ValueError):
                value = np.nan
            values.append(value if np.isfinite(value) else np.nan)
        return values

    all_girders = _group_girders(nodes, members)
    girder_names = {
        z_val: f"G{index + 1}"
        for index, (z_val, _) in enumerate(all_girders)
    }
    girders = _selected_girders(all_girders, girder_index)
    if not girders:
        return empty_contour("No girder contour data")

    rows = []
    common_x = None

    for z_val, elems in girders:
        girder_name = girder_names.get(z_val, f"G{len(rows) + 1}")
        points = []
        for elem in elems:
            try:
                n1, _ = members[elem]
            except (KeyError, TypeError, ValueError, IndexError):
                continue
            value_i, _ = get_force_pair(elem)
            points.append((float(nodes[n1][0]), value_i))

        if elems:
            try:
                last_elem = elems[-1]
                _, n2 = members[last_elem]
                _, value_j = get_force_pair(last_elem)
                points.append((float(nodes[n2][0]), value_j))
            except (KeyError, TypeError, ValueError, IndexError):
                pass

        if not points:
            continue

        xs = np.asarray([point[0] for point in points], dtype=float)
        values = np.asarray([point[1] for point in points], dtype=float)
        finite_x = np.isfinite(xs)
        if finite_x.sum() < 2:
            continue
        xs = xs[finite_x]
        values = values[finite_x]
        order = np.argsort(xs)
        xs = xs[order]
        values = values[order]
        xs, unique_indices = np.unique(xs, return_index=True)
        values = values[unique_indices]
        common_x = xs if common_x is None else np.union1d(common_x, xs)
        rows.append((girder_name, xs, values.astype(float)))

    if common_x is None or len(common_x) < 2 or not rows:
        return empty_contour("No finite contour data")

    contour_rows = []
    row_labels = []
    for girder_name, xs, values in rows:
        finite_value = np.isfinite(values)
        if finite_value.sum() == 0:
            continue
        if finite_value.sum() == 1:
            interpolated = np.full(common_x.shape, values[finite_value][0], dtype=float)
        else:
            interpolated = np.interp(
                common_x,
                xs[finite_value],
                values[finite_value],
            )
        contour_rows.append(interpolated * scale_factor)
        row_labels.append(girder_name)

    if not contour_rows:
        return empty_contour("No finite contour data")

    z_matrix = np.asarray(contour_rows, dtype=float)
    finite_values = z_matrix[np.isfinite(z_matrix)]
    if finite_values.size == 0:
        return empty_contour("No finite contour data")

    for row_index in range(z_matrix.shape[0]):
        row = z_matrix[row_index]
        valid = np.isfinite(row)
        if valid.all():
            continue
        if valid.any():
            z_matrix[row_index] = np.interp(
                np.arange(len(row)),
                np.where(valid)[0],
                row[valid],
            )
        else:
            z_matrix[row_index] = np.full(len(row), float(np.mean(finite_values)))

    if z_matrix.shape[0] == 1:
        z_matrix = np.vstack([z_matrix, z_matrix])
        y_vals = np.array([0, 1])
        y_labels = [row_labels[0], row_labels[0]]
    else:
        y_vals = np.arange(z_matrix.shape[0])
        y_labels = row_labels

    finite_x = np.isfinite(common_x)
    if finite_x.sum() < 2:
        return empty_contour("No finite contour span data")
    if not finite_x.all():
        common_x = common_x[finite_x]
        z_matrix = z_matrix[:, finite_x]

    if not np.isfinite(y_vals).all():
        return empty_contour("No finite contour girder data")

    finite_values = z_matrix[np.isfinite(z_matrix)]
    if finite_values.size == 0:
        return empty_contour("No finite contour data")
    replacement = float(np.mean(finite_values))
    z_matrix = np.nan_to_num(
        z_matrix,
        nan=replacement,
        posinf=replacement,
        neginf=replacement,
    )
    if z_matrix.shape != (len(y_vals), len(common_x)):
        return empty_contour("Invalid contour grid shape")

    finite_values = z_matrix[np.isfinite(z_matrix)]
    z_min = float(np.min(finite_values))
    z_max = float(np.max(finite_values))
    fig = go.Figure()
    if z_min == z_max:
        fig.update_layout(
            annotations=[
                dict(
                    text=f"No {force_key} contour variation",
                    x=0.5,
                    y=0.95,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                )
            ]
        )
        z_min -= 1.0
        z_max += 1.0

    z_matrix = np.clip(z_matrix, z_min, z_max)
    fig.add_trace(go.Contour(
        x=common_x.tolist(),
        y=y_vals.tolist(),
        z=z_matrix.tolist(),
        colorscale="Viridis",
        zmin=z_min,
        zmax=z_max,
        contours=dict(coloring="heatmap", showlabels=True),
        line_smoothing=0.85,
        connectgaps=True,
        colorbar=dict(title=force_key),
        hovertemplate=f"X=%{{x:.2f}}<br>Girder=%{{y}}<br>{force_key}=%{{z:.2f}}<extra></extra>",
        showlegend=False,
    ))

    fig.update_xaxes(title_text="Span Length")
    fig.update_yaxes(
        title_text="Girder",
        tickmode="array",
        tickvals=y_vals.tolist(),
        ticktext=y_labels,
    )
    _apply_contour_layout(fig, show_grid=show_grid)
    return fig.to_json()


# ============================================================
# BMD CONTOUR
# ============================================================
def build_figure_bmd_contour(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, girder_index=None):
    scale_factor = _finite_float(scale_factor, 1.0)

    if force_key.startswith("F"):
        return build_figure_force_contour(
            ds,
            force_key,
            nodes,
            members,
            show_grid=show_grid,
            scale_factor=scale_factor,
            girder_index=girder_index,
        )

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    girders = _selected_girders(_group_girders(nodes, members), girder_index)
    if not girders:
        return go.Figure().to_json()

    xfull, mzfull = [], []
    for _, elems in girders:
        xs, ys, zs, mz, _ = _build_polyline_for_girder(elems, nodes, members, comp_i, comp_j, get_force)
        xfull.extend(xs)
        mzfull.extend(mz)

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    master_drop_x, master_drop_y, master_drop_z, master_drop_color, master_drop_text = [], [], [], [], []
    master_base_x, master_base_y, master_base_z = [], [], []

    for i, (gid, elems) in enumerate(girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, mz, node_ids = _build_polyline_for_girder(elems, nodes, members, comp_i, comp_j, get_force)

        if max(mz) - min(mz) == 0:
            moment_scale = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * moment_scale * scale_factor

        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull),
            opacity=0.4, showscale=False, hoverinfo="skip", name=girder_name,
            legendgroup=girder_name, showlegend=True
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
            marker=dict(size=12, opacity=0),
            showlegend=False, text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}" for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text"
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[f"<b>{girder_name}</b>"],
            textposition="middle left", textfont=dict(size=14, color="black"),
            showlegend=False, hoverinfo="skip"
        ))

        master_base_x.extend([xs[0], xs[-1], None])
        master_base_y.extend([0, 0, None])
        master_base_z.extend([zs[0], zs[0], None])

        for xi, zi, mzi, nid in zip(xs, zs, mz, node_ids):
            master_drop_x.extend([xi, xi, None])
            master_drop_y.extend([0, mzi * moment_scale * scale_factor, None])
            master_drop_z.extend([zi, zi, None])
            master_drop_color.extend([mzi, mzi, mzi])
            htext = f"Node {nid}<br>X={xi:.2f}<br>{force_key}={mzi:.2f}"
            master_drop_text.extend([htext, htext, None])

    fig.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode="lines",
        line=dict(color="green", width=3), hoverinfo="skip", showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=master_drop_x, y=master_drop_y, z=master_drop_z, mode="lines+markers",
        line=dict(width=4, color=master_drop_color, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
        marker=dict(size=12, opacity=0), showlegend=False, text=master_drop_text, hoverinfo="text"
    ))

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", font_size=12, font_color="#F8F9FA", bordercolor="#0EA5E9", namelength=-1),
        scene=_scene_layout(show_grid),
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig.to_json()

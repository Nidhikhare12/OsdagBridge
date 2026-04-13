import numpy as np
import plotly.graph_objects as go
import openseespy.opensees as ops

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Vy": ("Vy_i", "Vy_j"),
    "Vz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
    "Tx": ("Mx_i", "Mx_j"),
    "Dx": ("dx", "dx"),
    "Dy": ("dy", "dy"),
    "Dz": ("dz", "dz"),
}

# ============================================================
# UNIFIED SCENE & CAMERA CONFIGURATION
# ============================================================
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
        hoverinfo='skip', showlegend=False, legendgroup='base'
    ))

def add_coordinate_triad(fig, nodes, scale=0.10):
    xs = [coord[0] for coord in nodes.values()]
    ys = [coord[1] for coord in nodes.values()]
    zs = [coord[2] for coord in nodes.values()]

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
            mode='lines', line=dict(color=color, width=5), hoverinfo='skip', showlegend=False, legendgroup='base'
        ))
        fig.add_trace(go.Cone(
            x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]], u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=L*0.2, anchor="tail", showscale=False, hoverinfo='skip',
            colorscale=[[0, color], [1, color]], legendgroup='base'
        ))

    draw_axis('X', [ox + L, oy, oz], [L, 0, 0], cad_colors['X'])
    draw_axis('Y', [ox, oy + L, oz], [0, L, 0], cad_colors['Y'])
    draw_axis('Z', [ox, oy, oz + L], [0, 0, L], cad_colors['Z'])

    fig.add_trace(go.Scatter3d(
        x=[ox + L*1.2, ox, ox], y=[oy, oy + L*1.2, oy], z=[oz, oz, oz + L*1.2],
        mode='text', text=['<b>X</b>', '<b>Y</b>', '<b>Z</b>'],
        textfont=dict(color=[cad_colors['X'], cad_colors['Y'], cad_colors['Z']], size=13, family="Arial Black, sans-serif"),
        hoverinfo='skip', showlegend=False, legendgroup='base'
    ))

def add_plot_controls(fig, num_girders, nodes):
    # Determine bounds for dynamic scaling
    xs = [c[0] for c in nodes.values()]
    zs = [c[2] for c in nodes.values()]
    span_x = max(xs) - min(xs)
    span_z = max(zs) - min(zs)
    z_ratio = span_z / span_x if span_x > 0 else 0.5
    
    girder_buttons = [
        dict(label="All Girders", method="restyle", args=[{"visible": set_all_visible(fig)}])
    ]
    for i in range(1, num_girders + 1):
        g_name = f"G{i}"
        girder_buttons.append(dict(label=g_name, method="restyle", args=[{"visible": set_girder_visible(fig, g_name)}]))

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons", direction="right", x=0.01, y=1.2, showactive=True, active=0,
                buttons=[
                    dict(label="Grid ON", method="relayout", args=[{"scene.xaxis.showgrid": True, "scene.zaxis.showgrid": True}]),
                    dict(label="Grid OFF", method="relayout", args=[{"scene.xaxis.showgrid": False, "scene.zaxis.showgrid": False}])
                ]
            ),
            dict(
                type="dropdown", direction="down", x=0.25, y=1.2, showactive=True, active=0,
                buttons=girder_buttons
            )
        ],
        sliders=[dict(
            active=2, x=0.45, y=1.2, len=0.4,
            currentvalue={"prefix": "Scale Y: "}, pad={"t": 0},
            steps=[
                dict(label=str(scale), method="relayout",
                     args=[{"scene.aspectmode": "manual", "scene.aspectratio": {"x": 1, "y": scale, "z": z_ratio}}])
                for scale in [0.25, 0.5, 1.0, 2.0, 4.0]
            ]
        )]
    )

def set_all_visible(fig):
    visible_array = []
    max_min_groups = ["max_lines", "min_lines"]
    for t in fig.data:
        lg = getattr(t, 'legendgroup', '')
        if lg in max_min_groups:
            visible_array.append(t.visible) # Keep their original visibility state
        else:
            visible_array.append(True)
    return visible_array

def set_girder_visible(fig, target_girder):
    visible_array = []
    max_min_groups = ["max_lines", "min_lines"]
    for t in fig.data:
        lg = getattr(t, 'legendgroup', '')
        if lg in max_min_groups:
            visible_array.append(t.visible)
        elif lg == 'base' or lg == target_girder:
            visible_array.append(True)
        elif lg and lg.startswith('G'):
            visible_array.append(False)
        else:
            visible_array.append(True)
    return visible_array

# ============================================================
# DATA HELPERS
# ============================================================
def extract_girders_and_polylines(ds, force_key, nodes, members, is_sfd=False):
    # This unified helper returns the polylines grouped by girder.
    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower(): return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP.get(force_key, ("Vy_i", "Vy_j"))
    comp_i, comp_j = find_component(comp_i_name), find_component(comp_j_name)

    Z_TOL = 3
    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    from collections import defaultdict
    girders = defaultdict(list)
    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    def get_force(elem, comp):
        if not comp: return 0.0
        try:
            return float(ds["forces"].sel(Element=elem, Component=comp).values)
        except Exception:
            return 0.0

    girder_data = []
    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    
    for i, (z_val, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elems:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elems[-1]
        n2 = members[last_e][1]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        
        girder_data.append((girder_name, np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids))
        
    return girder_data

# ============================================================
# SFD
# ============================================================
def build_figure_sfd(ds, force_key, nodes, members, show_max=False, show_min=False):
    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)
    
    girder_data = extract_girders_and_polylines(ds, force_key, nodes, members, is_sfd=True)
    all_vals = []
    for gd in girder_data: all_vals.extend(gd[4])
    cmin_val, cmax_val = min(all_vals), max(all_vals)
    
    summary_data = {}
    
    for girder_name, xs, ys, zs, vy, node_ids in girder_data:
        Vy = vy.astype(float)
        z_base = np.mean(zs)
        
        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        # ADDED CONTOUR FOR SFD: mapped colors to Vy_step
        fig.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[Vy_step, Vy_step], colorscale="Jet", cmin=cmin_val, cmax=cmax_val,
            opacity=0.4, showscale=False, hoverinfo="skip",
            legendgroup=girder_name, name=girder_name, showlegend=True
        ))
        
        # Base green line
        fig.add_trace(go.Scatter3d(
            x=list(xs), y=[0]*len(xs), z=list(zs), mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip", showlegend=False, legendgroup=girder_name
        ))

        hover_strings = [f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
                         for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])]

        # Colored contour lines
        fig.add_trace(go.Scatter3d(
            x=x_step, y=y_step, z=z_step, mode="lines",
            line=dict(width=6, color=Vy_step, colorscale="Jet", cmin=cmin_val, cmax=cmax_val),
            hoverinfo="text", text=hover_strings, showlegend=False, legendgroup=girder_name
        ))
        
        # Vertical drop lines
        cliff_x, cliff_y, cliff_z = [], [], []
        for xi, vyi in zip(xs, Vy):
            cliff_x.extend([xi, xi, None])
            cliff_z.extend([z_base, z_base, None])
            cliff_y.extend([0, -vyi * shear_scale if xi == xs[-1] else vyi * shear_scale, None])
            
        fig.add_trace(go.Scatter3d(
            x=cliff_x, y=cliff_y, z=cliff_z, mode="lines",
            line=dict(color="blue", width=4), hoverinfo="skip", showlegend=False, legendgroup=girder_name
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"),
            showlegend=False, hoverinfo="skip", legendgroup=girder_name
        ))
        
        summary_data[girder_name] = {"max": max(Vy), "min": min(Vy)}

    hud_text = build_hud_text(summary_data)
    add_plot_controls(fig, len(girder_data), nodes)
    
    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#E6F2FF", font_size=12, font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1),
        scene=SHARED_SCENE,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor="white", plot_bgcolor="white",
        annotations=[
            dict(
                x=0.02, y=0.95, xref="paper", yref="paper", text=hud_text, showarrow=False,
                bgcolor="rgba(33, 37, 43, 0.85)", bordercolor="rgba(255, 255, 255, 0.2)",
                borderwidth=1, borderpad=12,
                font=dict(family="Consolas, 'Courier New', monospace", size=12, color="white"),
                align="left", visible=False # Can build Output dock link if needed later
            )
        ],
    )
    return fig.to_json()


def build_hud_text(summary_data):
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
    return hud_text

# ============================================================
# BMD
# ============================================================
def build_figure_bmd(ds, force_key, nodes, members, show_max=False, show_min=False):
    fig_bmd = go.Figure()
    add_grillage_background(fig_bmd, nodes, members)
    add_coordinate_triad(fig_bmd, nodes)

    summary_data = {}
    girder_data = extract_girders_and_polylines(ds, force_key, nodes, members)

    for girder_name, xs, ys, zs, mz, node_ids in girder_data:
        if max(mz) - min(mz) == 0:
            factormz = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * factormz

        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1]*len(xs), [1]*len(xs)], colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            legendgroup=girder_name, name=girder_name, showlegend=True
        ))

        hover_text = [f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}" for nid, x, v, z in zip(node_ids, xs, mz, zs)]
        fig_bmd.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode='lines', line=dict(color="red", width=4),
            showlegend=False, text=hover_text, hoverinfo="text", legendgroup=girder_name
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode='lines',
            line=dict(color="green", width=3, dash='solid'), showlegend=False, hoverinfo='skip', legendgroup=girder_name
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"), showlegend=False, hoverinfo="skip", legendgroup=girder_name
        ))

        idx_max, max_val = np.argmax(mz), max(mz)
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[idx_max], xs[idx_max]], y=[0, max_val * factormz], z=[zs[0], zs[0]], mode="lines", line=dict(color="black", width=3),
            legendgroup="max_lines", showlegend=False, visible=show_max, hoverinfo="skip", name="MAX"
        ))

        idx_min, min_val = np.argmin(mz), min(mz)
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[idx_min], xs[idx_min]], y=[0, min_val * factormz], z=[zs[0], zs[0]], mode="lines", line=dict(color="black", width=3),
            legendgroup="min_lines", showlegend=False, visible=show_min, hoverinfo="skip", name="MIN"
        ))

        summary_data[girder_name] = {"max": max_val, "min": min_val}

    hud_text = build_hud_text(summary_data)
    add_plot_controls(fig_bmd, len(girder_data), nodes)

    fig_bmd.update_layout(
        uirevision="constant_view",
        annotations=[
            dict(
                x=0.02, y=0.95, xref="paper", yref="paper", text=hud_text, showarrow=False,
                bgcolor="rgba(33, 37, 43, 0.85)", bordercolor="rgba(255, 255, 255, 0.2)",
                borderwidth=1, borderpad=12,
                font=dict(family="Consolas, 'Courier New', monospace", size=12, color="white"),
                align="left", visible=False
            )
        ],
        hoverlabel=dict(bgcolor="#FFE4E1", font_size=12, font_color="#2C3E50", bordercolor="#CBD5E1", namelength=-1),
        scene=SHARED_SCENE,
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=60, b=0)
    )
    return fig_bmd.to_json(), summary_data


# ============================================================
# BMD CONTOUR
# ============================================================
def build_figure_bmd_contour(ds, force_key, nodes, members, show_max=False, show_min=False):
    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    girder_data = extract_girders_and_polylines(ds, force_key, nodes, members)
    all_mz = []
    for gd in girder_data: all_mz.extend(gd[4])
    cmin_val, cmax_val = min(all_mz), max(all_mz)
    summary_data = {}

    for girder_name, xs, ys, zs, mz, node_ids in girder_data:
        if max(mz) - min(mz) == 0:
            moment_scale = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * moment_scale

        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet", cmin=cmin_val, cmax=cmax_val,
            opacity=0.4, showscale=False, hoverinfo="skip",
            legendgroup=girder_name, name=girder_name, showlegend=True
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=cmin_val, cmax=cmax_val),
            marker=dict(size=12, opacity=0),
            showlegend=False, text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}" for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text", legendgroup=girder_name
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[f"<b>{girder_name}</b>"],
            textposition="middle left", textfont=dict(size=14, color="black"),
            showlegend=False, hoverinfo="skip", legendgroup=girder_name
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip", showlegend=False, legendgroup=girder_name
        ))

        drop_x, drop_y, drop_z, drop_color, drop_text = [], [], [], [], []
        for xi, zi, mzi, nid in zip(xs, zs, mz, node_ids):
            drop_x.extend([xi, xi, None])
            drop_y.extend([0, mzi * moment_scale, None])
            drop_z.extend([zi, zi, None])
            drop_color.extend([mzi, mzi, mzi])
            htext = f"Node {nid}<br>X={xi:.2f}<br>{force_key}={mzi:.2f}"
            drop_text.extend([htext, htext, None])

        fig.add_trace(go.Scatter3d(
            x=drop_x, y=drop_y, z=drop_z, mode="lines+markers",
            line=dict(width=4, color=drop_color, colorscale="Jet", cmin=cmin_val, cmax=cmax_val),
            marker=dict(size=12, opacity=0), showlegend=False, text=drop_text, hoverinfo="text", legendgroup=girder_name
        ))
        summary_data[girder_name] = {"max": max(mz), "min": min(mz)}
        
    add_plot_controls(fig, len(girder_data), nodes)

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", font_size=12, font_color="#F8F9FA", bordercolor="#0EA5E9", namelength=-1),
        scene=SHARED_SCENE,
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=60, b=0)
    )

    return fig.to_json(), summary_data

import numpy as np
import plotly.graph_objects as go
import openseespy.opensees as ops
import copy

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}

SHARED_SCENE = dict(
    camera=dict(
        up=dict(x=0, y=1, z=0),
        center=dict(x=0, y=0, z=0),
        eye=dict(x=0, y=0.1, z=2.5) 
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

def get_scene(show_grid=True):
    scene = copy.deepcopy(SHARED_SCENE)
    scene['xaxis']['showgrid'] = show_grid
    scene['xaxis']['zeroline'] = show_grid
    scene['zaxis']['showgrid'] = show_grid
    scene['zaxis']['zeroline'] = show_grid
    return scene

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
        hoverinfo='skip', showlegend=False
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

def add_plotly_controls(fig, has_contour=False, contour_indices=None, std_indices=None):
    num_traces = len(fig.data)
    
    girders = []
    for t in fig.data:
        if getattr(t, 'legendgroup', None) and getattr(t, 'legendgroup', '').startswith('G'):
            gname = t.legendgroup
            if gname not in girders: girders.append(gname)

    girder_buttons = [dict(
        label="All Girders", method="restyle",
        args=["visible", [True if not getattr(fig.data[i], 'legendgroup', '') in ['max_lines', 'min_lines'] else False for i in range(num_traces)]]
    )]
    for gname in girders:
        vis_arr = []
        for i in range(num_traces):
            grp = getattr(fig.data[i], 'legendgroup', None)
            if grp in ['max_lines', 'min_lines']: vis_arr.append(False)
            elif grp and grp.startswith('G'): vis_arr.append(grp == gname)
            else: vis_arr.append(True)
        girder_buttons.append(dict(label=gname, method="restyle", args=["visible", vis_arr]))

    grid_buttons = [
        dict(label="Grid ON", method="relayout", args=[{"scene.xaxis.showgrid": True, "scene.zaxis.showgrid": True, "scene.xaxis.zeroline": True, "scene.zaxis.zeroline": True}]),
        dict(label="Grid OFF", method="relayout", args=[{"scene.xaxis.showgrid": False, "scene.zaxis.showgrid": False, "scene.xaxis.zeroline": False, "scene.zaxis.zeroline": False}])
    ]
    
    contour_buttons = []
    if has_contour and contour_indices and std_indices:
        vis_std = [True] * num_traces
        vis_contour = [True] * num_traces
        for idx in contour_indices: vis_std[idx] = False
        for idx in std_indices: vis_contour[idx] = False
        
        for i in range(num_traces):
            grp = getattr(fig.data[i], 'legendgroup', None)
            if grp in ['max_lines', 'min_lines']:
                vis_std[i] = False
                vis_contour[i] = False
                
        contour_buttons = [
            dict(label="Lines", method="restyle", args=["visible", vis_std]),
            dict(label="Contour", method="restyle", args=["visible", vis_contour])
        ]

    menus = list(fig.layout.updatemenus) if fig.layout.updatemenus else []
    menus.append(dict(
        type="dropdown", direction="down", x=-0.05, y=1.0, showactive=True,
        buttons=girder_buttons, pad=dict(r=10, t=10)
    ))
    menus.append(dict(
        type="buttons", direction="right", x=-0.05, y=0.9, showactive=True,
        buttons=grid_buttons, pad=dict(r=10, t=10)
    ))
    if contour_buttons:
        menus.append(dict(
            type="buttons", direction="right", x=-0.05, y=0.85, showactive=True,
            buttons=contour_buttons, pad=dict(r=10, t=10)
        ))

    all_x, all_z = [], []
    for t in fig.data:
        if getattr(t, 'x', None) is not None:
            for val in np.array(t.x).ravel():
                if val is not None: all_x.append(val)
        if getattr(t, 'z', None) is not None:
            for val in np.array(t.z).ravel():
                if val is not None: all_z.append(val)
            
    if all_x and all_z:
        span_x, span_z = max(all_x) - min(all_x), max(all_z) - min(all_z)
        span_x, span_z = max(span_x, 1), max(span_z, 1)
        x_ratio, z_ratio = 1.0, span_z / span_x
    else:
        x_ratio, z_ratio = 1.0, 1.0

    steps = []
    for scale in [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0]:
        steps.append(dict(
            label=f"{scale}x", method="relayout",
            args=[{"scene.aspectmode": "manual", "scene.aspectratio": dict(x=x_ratio, y=scale, z=z_ratio)}]
        ))
    sliders = list(fig.layout.sliders) if fig.layout.sliders else []
    sliders.append(dict(
        active=3, currentvalue={"prefix": "Scale: "},
        pad={"t": 50}, steps=steps, x=0.0, y=-0.1, len=0.4
    ))
    fig.update_layout(updatemenus=menus, sliders=sliders)

def build_figure_sfd(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, isolated_girder="All", include_controls=True):
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

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    fig_sfd = go.Figure()
    add_grillage_background(fig_sfd, nodes, members)
    add_coordinate_triad(fig_sfd, nodes)

    std_indices = []
    contour_indices = []
    
    vfull = []
    for elems in girders.values():
        _, _, _, vy, _ = build_polyline(elems, comp_i, comp_j)
        vfull.extend(np.repeat(vy.astype(float)[:-1], 2))
    cmax, cmin = max(vfull) if vfull else 1, min(vfull) if vfull else -1

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (z_val, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        is_visible = True if isolated_girder in ["All", girder_name] else False
        
        xs, ys, zs, vy, node_ids = build_polyline(elems, comp_i, comp_j)
        Vy = vy.astype(float)
        z_base = np.mean(zs)

        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))
            
        shear_scale *= scale_factor

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        idx_start = len(fig_sfd.data)
        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[[1]*len(y_step), [1]*len(y_step)], colorscale=[[0, 'blue'], [1, 'blue']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=True, visible=is_visible
        ))

        hover_strings = [f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
                         for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])]

        fig_sfd.add_trace(go.Scatter3d(
            x=x_step, y=y_step, z=z_step, mode="lines",
            line=dict(color="blue", width=6), hoverinfo="text", text=hover_strings,
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible
        ))
        
        fig_sfd.add_trace(go.Scatter3d(
            x=xs, y=[0]*len(xs), z=zs, mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible
        ))

        cliff_x, cliff_y, cliff_z = [], [], []
        for xi, vyi in zip(xs, Vy):
            cliff_x.extend([xi, xi, None])
            cliff_z.extend([z_base, z_base, None])
            cliff_y.extend([0, -vyi * shear_scale if xi == xs[-1] else vyi * shear_scale, None])

        fig_sfd.add_trace(go.Scatter3d(
            x=cliff_x, y=cliff_y, z=cliff_z, mode="lines",
            line=dict(color="blue", width=4), hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible
        ))

        fig_sfd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text",
            text=[girder_name], textposition="middle left", textfont=dict(size=11, color="black"),
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible, hoverinfo="skip"
        ))
        std_indices.extend(list(range(idx_start, len(fig_sfd.data))))

        idx_start_c = len(fig_sfd.data)
        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[Vy_step, Vy_step], colorscale="Jet", cmin=cmin, cmax=cmax,
            opacity=0.4, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=False
        ))
        
        fig_sfd.add_trace(go.Scatter3d(
            x=x_step, y=y_step, z=z_step, mode="lines+markers",
            line=dict(width=6, color=Vy_step, colorscale="Jet", cmin=cmin, cmax=cmax),
            marker=dict(size=12, opacity=0),
            hoverinfo="text", text=hover_strings,
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=False
        ))

        fig_sfd.add_trace(go.Scatter3d(
            x=xs, y=[0]*len(xs), z=zs, mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=False
        ))

        drop_x, drop_y, drop_z, drop_color = [], [], [], []
        for xi, vyi in zip(xs, Vy):
            vy_val = -vyi if xi == xs[-1] else vyi
            drop_x.extend([xi, xi, None])
            drop_z.extend([z_base, z_base, None])
            drop_y.extend([0, vy_val * shear_scale, None])
            drop_color.extend([vyi, vyi, vyi])

        fig_sfd.add_trace(go.Scatter3d(
            x=drop_x, y=drop_y, z=drop_z, mode="lines",
            line=dict(color=drop_color, width=4, colorscale="Jet", cmin=cmin, cmax=cmax), hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=False
        ))

        fig_sfd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text",
            text=[f"<b>{girder_name}</b>"], textposition="middle left", textfont=dict(size=14, color="black"),
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=False, hoverinfo="skip"
        ))
        contour_indices.extend(list(range(idx_start_c, len(fig_sfd.data))))

    fig_sfd.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#E6F2FF", font_size=12, font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1),
        scene=get_scene(show_grid),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", groupclick="togglegroup"),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="white", plot_bgcolor="white"
    )
    if include_controls:
        add_plotly_controls(fig_sfd, has_contour=True, contour_indices=contour_indices, std_indices=std_indices)
    return fig_sfd.to_json()

def build_figure_bmd(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, isolated_girder="All", show_max=False, show_min=False, include_controls=True):
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

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    fig_bmd = go.Figure()
    add_grillage_background(fig_bmd, nodes, members)
    add_coordinate_triad(fig_bmd, nodes)

    summary_data = {}

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (gid, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        is_visible = True if isolated_girder in ["All", girder_name] else False
        
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            factormz = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
            
        factormz *= scale_factor

        y_plot = mz * factormz

        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1]*len(xs), [1]*len(xs)], colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=True, visible=is_visible
        ))

        hover_text = [f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}" for nid, x, v, z in zip(node_ids, xs, mz, zs)]
        
        fig_bmd.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode='lines', line=dict(color="red", width=4),
            showlegend=False, text=hover_text, hoverinfo="text",
            name=girder_name, legendgroup=girder_name, visible=is_visible
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode='lines',
            line=dict(color="green", width=3, dash='solid'), showlegend=False, hoverinfo='skip',
            name=girder_name, legendgroup=girder_name, visible=is_visible
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"), 
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, visible=is_visible
        ))

        idx_max, max_val = np.argmax(mz), max(mz)
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[idx_max], xs[idx_max]], y=[0, max_val * factormz], z=[zs[0], zs[0]], 
            mode="lines", line=dict(color="black", width=3),
            legendgroup="max_lines", showlegend=False, visible=False, hoverinfo="skip"
        ))

        idx_min, min_val = np.argmin(mz), min(mz)
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[idx_min], xs[idx_min]], y=[0, min_val * factormz], z=[zs[0], zs[0]], 
            mode="lines", line=dict(color="black", width=3),
            legendgroup="min_lines", showlegend=False, visible=False, hoverinfo="skip"
        ))

        summary_data[girder_name] = {"max": max_val, "min": min_val}

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
                    dict(label="SUMMARY", method="relayout", args=[{"annotations[0].visible": True}], args2=[{"annotations[0].visible": False}]),
                ]
            )
        ] if include_controls else [],
        scene=get_scene(show_grid),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", groupclick="togglegroup"),
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )
    for trace in fig_bmd.data:
        if getattr(trace, "legendgroup", None) == "max_lines":
            trace.visible = show_max
        elif getattr(trace, "legendgroup", None) == "min_lines":
            trace.visible = show_min

    if include_controls:
        add_plotly_controls(fig_bmd, has_contour=False)
    return fig_bmd.to_json(), summary_data


def build_figure_sfd_contour(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, isolated_girder="All", include_controls=True):
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

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1)
            ys.append(y1)
            zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2)
        ys.append(y2)
        zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    vfull = []
    for elems in girders.values():
        _, _, _, vy, _ = build_polyline(elems, comp_i, comp_j)
        vfull.extend(np.repeat(vy.astype(float)[:-1], 2))
    cmax, cmin = max(vfull) if vfull else 1, min(vfull) if vfull else -1

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (_, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        is_visible = isolated_girder in ["All", girder_name]

        xs, ys, zs, vy, node_ids = build_polyline(elems, comp_i, comp_j)
        Vy = vy.astype(float)
        z_base = np.mean(zs)

        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))
        shear_scale *= scale_factor

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        hover_strings = [
            f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
            for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])
        ]

        fig.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[Vy_step, Vy_step], colorscale="Jet", cmin=cmin, cmax=cmax,
            opacity=0.4, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=True, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=x_step, y=y_step, z=z_step, mode="lines+markers",
            line=dict(width=6, color=Vy_step, colorscale="Jet", cmin=cmin, cmax=cmax),
            marker=dict(size=12, opacity=0),
            hoverinfo="text", text=hover_strings,
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=[0] * len(xs), z=zs, mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible,
        ))

        drop_x, drop_y, drop_z, drop_color = [], [], [], []
        for xi, vyi in zip(xs, Vy):
            vy_val = -vyi if xi == xs[-1] else vyi
            drop_x.extend([xi, xi, None])
            drop_z.extend([z_base, z_base, None])
            drop_y.extend([0, vy_val * shear_scale, None])
            drop_color.extend([vyi, vyi, vyi])

        fig.add_trace(go.Scatter3d(
            x=drop_x, y=drop_y, z=drop_z, mode="lines",
            line=dict(color=drop_color, width=4, colorscale="Jet", cmin=cmin, cmax=cmax),
            hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text",
            text=[f"<b>{girder_name}</b>"], textposition="middle left", textfont=dict(size=14, color="black"),
            name=girder_name, legendgroup=girder_name, showlegend=False, visible=is_visible, hoverinfo="skip",
        ))

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#E6F2FF", font_size=12, font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1),
        scene=get_scene(show_grid),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", groupclick="togglegroup"),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="white", plot_bgcolor="white",
    )
    if include_controls:
        add_plotly_controls(fig, has_contour=False)
    return fig.to_json()


def build_figure_bmd_contour(ds, force_key, nodes, members, show_grid=True, scale_factor=1.0, isolated_girder="All", include_controls=True):
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

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1)
            ys.append(y1)
            zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2)
        ys.append(y2)
        zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    mfull = []
    for elems in girders.values():
        _, _, _, mz, _ = build_polyline(elems, comp_i, comp_j)
        mfull.extend(mz.astype(float))
    cmax, cmin = max(mfull) if mfull else 1, min(mfull) if mfull else -1

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (_, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        is_visible = isolated_girder in ["All", girder_name]
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            moment_scale = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
        moment_scale *= scale_factor

        y_plot = mz * moment_scale

        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet", cmin=cmin, cmax=cmax,
            opacity=0.4, showscale=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, showlegend=True, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=cmin, cmax=cmax),
            marker=dict(size=12, opacity=0),
            showlegend=False,
            text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}" for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text",
            name=girder_name, legendgroup=girder_name, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip", showlegend=False,
            name=girder_name, legendgroup=girder_name, visible=is_visible,
        ))

        drop_x, drop_y, drop_z, drop_color = [], [], [], []
        for xi, zi, mzi in zip(xs, zs, mz):
            drop_x.extend([xi, xi, None])
            drop_y.extend([0, mzi * moment_scale, None])
            drop_z.extend([zi, zi, None])
            drop_color.extend([mzi, mzi, mzi])

        fig.add_trace(go.Scatter3d(
            x=drop_x, y=drop_y, z=drop_z, mode="lines",
            line=dict(width=4, color=drop_color, colorscale="Jet", cmin=cmin, cmax=cmax),
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, visible=is_visible,
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[f"<b>{girder_name}</b>"],
            textposition="middle left", textfont=dict(size=14, color="black"),
            showlegend=False, hoverinfo="skip",
            name=girder_name, legendgroup=girder_name, visible=is_visible,
        ))

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#FFE4E1", font_size=12, font_color="#2C3E50", bordercolor="#CBD5E1", namelength=-1),
        scene=get_scene(show_grid),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", groupclick="togglegroup"),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="white", plot_bgcolor="white",
    )
    if include_controls:
        add_plotly_controls(fig, has_contour=False)
    return fig.to_json()
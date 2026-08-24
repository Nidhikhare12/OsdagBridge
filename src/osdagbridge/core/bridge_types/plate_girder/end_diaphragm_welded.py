import copy
import math
from osdagbridge.core.utils.common import (
    KEY_MP_ED_TOTAL_DEPTH, KEY_MP_ED_WEB_THICKNESS, KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS, KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H,
    KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF, KEY_TD_ED_PROP_M,
    KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV, KEY_TD_ED_PROP_RZ,
    KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ,
    KEY_TD_ED_PROP_ZUV
)
from osdagbridge.core.utils.connect import design_dict_plate_girder

def process_welded_diaphragm(bridge, pair, pair_id, member_suffix, max_vy, max_mz, s, make_pair_key, jobs):
    depth = float(bridge.input_dict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{member_suffix}") or 0.0)
    web_t = float(bridge.input_dict.get(f"{KEY_MP_ED_WEB_THICKNESS}{member_suffix}") or 0.0)
    top_w = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{member_suffix}") or 0.0)
    bot_w = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{member_suffix}") or 0.0)
    top_t = float(bridge.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{member_suffix}") or 0.0)
    bot_t = float(bridge.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{member_suffix}") or 0.0)

    if depth > 0:
        h_w = depth - top_t - bot_t
        a_f1 = top_w * top_t
        a_f2 = bot_w * bot_t
        a_w = h_w * web_t
        a_total = a_f1 + a_f2 + a_w

        if max_vy > 0 or max_mz > 0:
            d = copy.deepcopy(design_dict_plate_girder)
            d["Load.Shear"] = str(max_vy)
            d["Load.Moment"] = str(max_mz)
            d["Member.Length"] = str(s)
            d["Total.Design_Type"] = "Customized" # Bypasses PySide PSO dialog crash
            d["IntermediateStiffener.Thickness"] = "All" # Bypasses QDialog popup
            d["LongitudnalStiffner.Thickness"] = "All" # Bypasses QDialog popup
            if depth > 0:
                d["Plate.Thickness"] = str(max(top_t, bot_t))
                d["Web.Thickness"] = str(web_t)
                d["Plate.Width"] = str(max(top_w, bot_w))
                d["Web.Depth"] = str(depth - top_t - bot_t)
            jobs.append((pair, "WeldedBeam", "flexure", d))

        y_f2 = bot_t / 2.0
        y_w = bot_t + h_w / 2.0
        y_f1 = depth - top_t / 2.0
        y_c = (a_f2 * y_f2 + a_w * y_w + a_f1 * y_f1) / a_total

        i_z = (1.0 / 12.0) * bot_w * (bot_t ** 3) + a_f2 * ((y_c - y_f2) ** 2) + \
            (1.0 / 12.0) * web_t * (h_w ** 3) + a_w * ((y_c - y_w) ** 2) + \
            (1.0 / 12.0) * top_w * (top_t ** 3) + a_f1 * ((y_c - y_f1) ** 2)

        i_y = (1.0 / 12.0) * bot_t * (bot_w ** 3) + \
            (1.0 / 12.0) * h_w * (web_t ** 3) + \
            (1.0 / 12.0) * top_t * (top_w ** 3)

        r_z = math.sqrt(i_z / a_total)
        r_y = math.sqrt(i_y / a_total)

        z_z = i_z / max(y_c, depth - y_c)
        z_y = i_y / max(top_w / 2.0, bot_w / 2.0)

        if abs(a_f2 - a_f1) < 1e-3:
            z_pz = top_w * top_t * (depth - top_t) + 0.25 * web_t * ((depth - 2.0 * top_t) ** 2)
        else:
            y_p = bot_t + (a_total / 2.0 - a_f2) / web_t
            z_pz = a_f2 * (y_p - bot_t / 2.0) + 0.5 * web_t * ((y_p - bot_t) ** 2) + \
                a_f1 * (depth - y_p - top_t / 2.0) + 0.5 * web_t * ((depth - y_p - top_t) ** 2)

        z_py = 0.25 * top_t * (top_w ** 2) + 0.25 * bot_t * (bot_w ** 2) + 0.25 * h_w * (web_t ** 2)
        mass = a_total * 0.00785

        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = depth / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = top_w / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = web_t / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = top_t / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = mass
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = a_total / 100.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = i_z / 10000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = i_y / 10000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = r_z / 10.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = r_y / 10.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = z_z / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = z_y / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = z_pz / 1000.0
        bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = z_py / 1000.0

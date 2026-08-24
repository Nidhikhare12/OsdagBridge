import copy
from osdagbridge.core.utils.common import (
    KEY_MP_ED_IS_SECTION, KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B,
    KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A,
    KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV, KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_RV,
    KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV
)
from osdagbridge.core.utils.connect import design_dict_simply_supported

def process_rolled_diaphragm(bridge, pair, pair_id, member_suffix, max_vy, max_mz, s, make_pair_key, _query_rolled_beam_section, jobs):
    is_sec_des = bridge.input_dict.get(f"{KEY_MP_ED_IS_SECTION}{member_suffix}")
    if is_sec_des:
        bridge.output_dict[make_pair_key(KEY_MP_ED_IS_SECTION, pair_id)] = is_sec_des
        # Note: _query_rolled_beam_section takes bridge and is_sec_des
        beam_details = _query_rolled_beam_section(bridge, is_sec_des)
        if beam_details:
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = beam_details["H"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = beam_details["B"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = beam_details["tw"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = beam_details["tF"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = beam_details["M"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = beam_details["A"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = beam_details["Iz"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = beam_details["Iv"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = beam_details["rz"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = beam_details["rv"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = beam_details["Zz"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = beam_details["Zv"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = beam_details["Zuz"]
            bridge.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = beam_details["Zuv"]

            if max_vy > 0 or max_mz > 0:
                d = copy.deepcopy(design_dict_simply_supported)
                d["Load.Shear"] = str(max_vy)
                d["Load.Moment"] = str(max_mz)
                d["Member.Length"] = str(s)
                if is_sec_des:
                    d["Member.Designation"] = [is_sec_des]
                jobs.append((pair, "RolledBeam", "flexure", d))

# optimiser.py
# optimisation design pipeline for OsdagBridge
# design vector = [D, bf_top, bf_bot, tf_top, tf_bot, tw] per girder

import math
import numpy as np
from osdagbridge.core.bridge_types.plate_girder.designer import (
    SteelSection,
    StiffenerConfig,
    IRC22CapacityCalculator,
    DCREngine,
    DemandEnvelope,
    build_deflections_cache,
    apply_camber_to_deflections_cache,
    _extract_demands_from_result_data,
)
from dataclasses import replace
from osdagbridge.core.utils.common import SAIL_APPROVED_THICKNESS_VALUES
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.designer import BridgeConfig
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_DEPTH,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_COMP_I,
    )
from osdagbridge.core.utils.common import DEFAULT_STEEL_DENSITY
from osdagbridge.core.bridge_types.plate_girder.initial_sizing import steel_i_section_properties
from osdagbridge.core.bridge_types.plate_girder.results_data import composite_stiffness_props

# -------------------------------------------------------------------------------------------------------
def sqrt(x):
    try:
        return math.sqrt(x)
    except ValueError:
        return 0.0  # Returns NaN for negative values

def _ceiling_plate(value_mm: float, _STD_PLATES = SAIL_APPROVED_THICKNESS_VALUES) -> float:
    """Smallest IS 2062 plate thickness ≥ value_mm (always structurally safe)."""
    for p in _STD_PLATES:
        if float(p) >= value_mm:
            return float(p)
    return float(_STD_PLATES[-1])

def _round_plate(value_mm, _STD_PLATES = SAIL_APPROVED_THICKNESS_VALUES):
    return float(min(_STD_PLATES, key=lambda p: abs(float(p) - value_mm)))

def _ceil(v: float, n: float = 10.0) -> float:
    """Ceil to nearest multiple of n."""
    return float(math.ceil(v / n) * n)


def _floor(v: float, n: float = 10.0) -> float:
    """Round to nearest multiple of n."""
    return float(math.floor(v / n) * n)


def clamp(v: float, lo: float, hi: float) -> float:
    """Hard-clip v to [lo, hi]."""
    return max(lo, min(v, hi))

def _get(inp: dict, key: str, default):
    
    try:
        return inp.get(key, default)
    except Exception:
        return default

# -------------------------------------------------------------------------------------------------------
# design vector = [D, bf_top, bf_bot, tf_top, tf_bot, tw] per girder

def create_upper_bound_array(inp: dict, idx: int, epsilon: float, span_length: float, bounds: dict)  -> np.ndarray:
    
    tf_top_list = bounds[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx+1}.M1']
    tf_bot_list = bounds[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx+1}.M1']
    tw_list = bounds[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx+1}.M1']
    
    idx += 1
    
    upper_depth = _get(_get(inp, f'{KEY_MP_GIRDER_DEPTH}.G{idx}.M1',{}),'upper',np.inf)
    D = min((span_length * 1000) / 15, upper_depth) # Assumption
    
    upper_bf_top = _get(_get(inp,f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{idx}.M1',{}),'upper',np.inf)
    bf_top = min(_ceil(0.5 * D, 50), upper_bf_top)
    
    upper_bf_bot = _get(_get(inp,f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{idx}.M1',{}),'upper',np.inf)
    bf_bot = min(_ceil(0.5 * D, 50), upper_bf_bot)
    
    upper_tf_top = _get(_get(inp,f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx}.M1',{}),'upper',np.inf)
    tf_top = min(_round_plate(bf_top / 24, tf_top_list), upper_tf_top)
    
    upper_tf_bot = _get(_get(inp,f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx}.M1',{}),'upper',np.inf)
    tf_bot = min(_round_plate(bf_bot / 24, tf_bot_list), upper_tf_bot)
    
    tw = _round_plate((D - tf_top - tf_bot) / (200 * epsilon), tw_list)
    
    return np.array([D, bf_top, bf_bot, tf_top, tf_bot, tw])

# -------------------------------------------------------------------------------------------------------
# def create_initial_vector(inp: dict, epsilon: float, idx: float) -> np.ndarray:

#     idx += 1
#     span_length = inp[KEY_SPAN]
#     default_depth = (span_length * 1000) / 18
#     D = inp.get(f'{KEY_MP_GIRDER_DEPTH}.G{idx}.M1', default_depth)
#     bf_top = inp.get(f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{idx}.M1', _ceil(0.3 * D, 50))
#     bf_bot = inp.get(f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{idx}.M1',_ceil(0.3 * D, 50))
#     tf_top = inp.get(f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx}.M1', _round_plate(bf_top / (24 * epsilon)))
#     tf_bot = inp.get(f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx}.M1',_round_plate(bf_bot / (24 * epsilon)))
#     tw = inp.get(f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx}.M1', _round_plate((D - tf_top - tf_bot) / (200 * epsilon)))
    
#     # D = default_depth
#     # bf_top = _ceil(0.4 * D, 50)
#     # bf_bot = _ceil(0.4 * D, 50)
#     # tf_top = _round_plate(bf_top / (24 * epsilon))
#     # tf_bot = _round_plate(bf_bot / (24 * epsilon))
#     # tw = _round_plate((D - tf_top - tf_bot) / (200 * epsilon))
#     return np.array([D, bf_top, bf_bot, tf_top, tf_bot, tw])

# -------------------------------------------------------------------------------------------------------
def create_lower_bound_array(inp: dict, idx: int, epsilon: float, span_length: float, bounds: dict) -> np.ndarray:
    
    tf_top_list = bounds[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx+1}.M1']
    tf_bot_list = bounds[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx+1}.M1']
    tw_list = bounds[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx+1}.M1']
    
    idx += 1
    lower_depth = _get(_get(inp,f'{KEY_MP_GIRDER_DEPTH}.G{idx}.M1',{}),'lower',5)
    D = max((span_length * 1000) / 30, lower_depth) # IRC 22
    
    lower_bf_top = _get(_get(inp,f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{idx}.M1',{}),'lower',0)
    bf_top = max(lower_bf_top,_ceil(0.3 * D, 50))
    
    lower_bf_bot = _get(_get(inp,f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{idx}.M1',{}),'lower',0)
    bf_bot = max(_ceil(0.3 * D, 50), lower_bf_bot)
    
    lower_tf_top = _get(_get(inp,f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx}.M1',{}),'lower',0)
    tf_top = max(_round_plate(bf_top / (24 * epsilon), tf_top_list), lower_tf_top)
    
    lower_tf_bot = _get(_get(inp,f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx}.M1',{}),'lower',0)
    tf_bot = max(_round_plate(bf_bot / (24 * epsilon), tf_bot_list), lower_tf_bot)
    
    tw = _round_plate((D - tf_top - tf_bot) / (200 * epsilon), tw_list)
    
    return np.array([D, bf_top, bf_bot, tf_top, tf_bot, tw])

def create_initial_vector(inp: dict, idx) -> np.ndarray:
    
    idx += 1
    D = inp[f'{KEY_MP_GIRDER_DEPTH}.G{idx}.M1']
    bf_top = inp[f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{idx}.M1']
    bf_bot = inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{idx}.M1']
    tf_top = inp[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx}.M1']
    tf_bot = inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx}.M1']
    tw = inp[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx}.M1']
    
    return np.array([D, bf_top, bf_bot, tf_top, tf_bot, tw])

# -------------------------------------------------------------------------------------------------------
# create dict with optimised values
# design vector = [D, bf_top, bf_bot, tf_top, tf_bot, tw] per girder
def update_dict(idx: int, inp: dict, x: np.ndarray, bounds: dict, lb: np.ndarray, ub: np.ndarray):
    
    tf_top_list = bounds[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx+1}.M1']
    tf_bot_list = bounds[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx+1}.M1']
    tw_list = bounds[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx+1}.M1']
    
    idx += 1
    D = clamp(_ceil(x[0], 10), _ceil(lb[0]), _floor(ub[0])) # / 1e3
    inp[f'{KEY_MP_GIRDER_DEPTH}.G{idx}.M1'] = D
    bf_top = clamp(_ceil(x[1], 5), _ceil(lb[1],5), _floor(ub[1])) # / 1e3
    inp[f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{idx}.M1'] = bf_top
    bf_bot = clamp(_ceil(x[2], 5), _ceil(lb[2]), _floor(ub[2])) # / 1e3
    inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{idx}.M1'] = bf_bot
    tf_top = clamp(_round_plate(x[3], tf_top_list), lb[3], ub[3]) # / 1e3
    inp[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx}.M1'] = tf_top
    tf_bot = clamp(_round_plate(x[4], tf_bot_list), lb[4], ub[4]) # / 1e3
    inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx}.M1'] = tf_bot
    tw = clamp(_round_plate(x[5], tw_list), lb[5], ub[5]) # / 1e3
    inp[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx}.M1'] = tw
    
    props = steel_i_section_properties(D / 1e3, bf_top / 1e3, tf_top / 1e3, bf_bot / 1e3, tf_bot / 1e3, tw / 1e3)
    for key, value in props.items():
        inp[f'{key}.G{idx}.M1'] = value
    dw = D - tf_top - tf_bot
    inp[f'{KEY_MP_GIRDER_WEB_DEPTH}.G{idx}.M1'] = dw
    g_area = inp[f'{KEY_MP_GIRDER_SECTIONAL_AREA}.G{idx}.M1'] # in m2
    
    print(f'Girder G{idx} optimised self weight = {g_area * DEFAULT_STEEL_DENSITY} kN per m')
    
    if idx == 1:
        
        inp[f'{KEY_MP_GIRDER_DEPTH}'] = D
        inp[f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}'] = bf_top
        inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}'] = bf_bot
        inp[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}'] = tf_top
        inp[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}'] = tf_bot
        inp[f'{KEY_MP_GIRDER_WEB_THICKNESS}'] = tw
        dw = D - tf_top - tf_bot
        inp[f'{KEY_MP_GIRDER_WEB_DEPTH}'] = dw
        
        props = steel_i_section_properties(D / 1e3, bf_top / 1e3, tf_top / 1e3, bf_bot / 1e3, tf_bot / 1e3, tw / 1e3)
        for key, value in props.items():
            inp[f'{key}'] = value
        dw = D - tf_top - tf_bot
        inp[KEY_MP_GIRDER_WEB_DEPTH] = dw

# -------------------------------------------------------------------------------------------------------
"""
    1. Adjust the stale demands based on the current SteelSection being evaluated. Approximation only, not exact.
    2. For shorter spans delta_live_mm becomes the critical check and for medium and longer spans M_construction_kN_m 
        and M_girder_sw_kNm tend to become the critical check.
"""

def adjust_demands(demand:DemandEnvelope, config: BridgeConfig, girder_section: SteelSection):
    
    area_original = config.section.A_steel / 1e6 # area in m^2
    area = girder_section.A_steel / 1e6 # area in m^2
    original_props, _ = composite_stiffness_props(config)
    Iz_original = config.section.Iz_steel   # in mm^2
    I_comp_original = original_props[KEY_COMP_I]     # second moment of inertia along strong axis of original composite section in mm^2
    config.section = girder_section
    girder_props, _ = composite_stiffness_props(config)
    Iz_girder = girder_section.Iz_steel # in mm^2
    I_comp_girder = girder_props[KEY_COMP_I]     # second moment of inertia along strong axis of composite section in mm^2
    
    demand.M_girder_sw_kNm *= (area / area_original)
    demand.M_construction_kNm -= config.geometry.span * config.geometry.span * (area_original - area) * DEFAULT_STEEL_DENSITY / 8
    # demand.Mu_kNm = demand.Mu_kNm - config.geometry.cross_bracing_spacing_m * config.geometry.cross_bracing_spacing_m * (area_original - area) * DEFAULT_STEEL_DENSITY / 8
    # demand.Mx_kNm *= (area / area_original)
    # demand.Vu_kN = demand.Vu_kN - config.geometry.span * (area_original - area) * DEFAULT_STEEL_DENSITY * 0.5
    
    moi_ratio = max(1.0, ( I_comp_original / I_comp_girder ), (Iz_original / Iz_girder)) # second moment of inertia ratio
    demand.delta_live_mm *= moi_ratio   # updates with value of current section

# -------------------------------------------------------------------------------------------------------
    
def objective_function(g_demand: DemandEnvelope, g_config:BridgeConfig, x: np.ndarray) -> float:
    
    D, bf_top, bf_bot, tf_top, tf_bot, tw = x[0], x[1], x[2], x[3], x[4], x[5]
    # s_stiffener, t_stiffener = x[6], x[7]   # stiffner spacing and thickness of stiffener plate
    
    # build the girder section
    girder_section = SteelSection(D, bf_top, tf_top, bf_bot, tf_bot, tw)
    # stiffener = StiffenerConfig(c_mm = s_stiffener, tq_mm= t_stiffener, shear_method= 'post_critical')
    
    # g_config.stiffener = stiffener
    demand = replace(g_demand)  # copy of demand object
    config = replace(g_config)  # copy of config object
    adjust_demands(demand, config, girder_section)
    config.section = girder_section
    
    # calculate the capacity and evaluate utility
    capacity_calculator = IRC22CapacityCalculator(config)
    if capacity_calculator.classify_section()['governing_class'] == 'Slender':
        print("Slender")
        return float(np.inf)
    
    capacity = capacity_calculator.compute_all( Vu_kN=demand.Vu_kN, stress_range_MPa=demand.stress_range_MPa,
                M_sls_kNm=demand.M_sls_kNm, V_sls_kN=demand.V_sls_kN, Vr_kN=demand.Vr_kN,)
    capacity.stud_detailing_ok = True   # to bypass the stud detailing checks for now

    # run DCR checks
    engine = DCREngine(demand, capacity)
    engine.run_all_checks()
    
    if engine.max_dcr() >= 1.0:
        return float(np.inf)

    g_area = (D - tf_top - tf_bot) * tw + bf_top * tf_top + bf_bot * tf_bot
    return g_area


def optimise_girder_dimensions(pgb: PlateGirderBridge, bounds: dict, run: int):
    
    result_data = getattr(pgb, "result_data", None)
    config = BridgeConfig.from_plate_girder_bridge(pgb)

    span = pgb.input_dict[KEY_SPAN]
    deflections_cache = apply_camber_to_deflections_cache(
                build_deflections_cache(config, result_data), config.geometry.camber_mode, config.geometry.camber_value_mm,
            )
    pgb._deflections_cache = deflections_cache
    
    per_girder_demands, per_girder_per_lc = _extract_demands_from_result_data( config, deflections_cache, result_data)
    result_dict: dict = {}
    
    from osdagbridge.core.bridge_types.plate_girder.pso import PSO
    for idx, (g_name, g_demand) in enumerate(per_girder_demands.items()):
        
        tf_top_list = bounds[f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{idx+1}.M1']
        tf_bot_list = bounds[f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{idx+1}.M1']
        tw_list = bounds[f'{KEY_MP_GIRDER_WEB_THICKNESS}.G{idx+1}.M1']
        
        if pgb is not None:
            try:
                g_config = BridgeConfig.from_plate_girder_bridge(pgb, girder_index=idx)
                if g_config.stiffener is None:
                    g_config.stiffener = StiffenerConfig(shear_method='post_critical')
                g_config.stiffener.bs_R_kN = config.stiffener.bs_R_kN
            except Exception:
                g_config = config
        else:
            g_config = config

        epsilon = sqrt(250 / g_config.material.fy)
        
        upper_bound_vector = create_upper_bound_array(bounds, idx, epsilon, span, bounds)
        lower_bound_vector = create_lower_bound_array(bounds, idx, epsilon, span, bounds)
            
        def snap(x):
            nonlocal epsilon
            x = x.copy()
            x[3] = _round_plate(x[3], tf_top_list) # tf_top
            x[4] = _round_plate(x[4], tf_bot_list) # tf_bot
            x[5] = _round_plate(x[5], tw_list) # tw
            x[0] =  min(x[5] * 126 * epsilon, x[0] - x[3] - x[4]) + x[3] + x[4] # D
            x[1] =  (min(x[3] * 13.6 * epsilon, (x[1] - x[5]) * 0.5)) * 2 + x[5] # bf_top
            x[2] =  (min(x[4] * 13.6 * epsilon, (x[2] - x[5]) * 0.5)) * 2 + x[5] # bf_bot
            return x

        initial_vector = create_initial_vector(pgb.input_dict, idx)
        optimizer = PSO(
            objective_function=lambda x: objective_function(g_demand, g_config, x),
            design_vector=initial_vector,
            lower_bounds=lower_bound_vector,
            upper_bounds=upper_bound_vector,
            repair=snap,
            extra_seeds=[upper_bound_vector],
            n_particles=40, max_iter=60,
            gname = g_name,
            min_feasible_frac= 0.5 - run * 0.15,
            tol = 1,
            run = run
        )
        best_x, best_f = optimizer.optimize()
        if best_f == np.inf:
            print(f"No optimal solution found for {g_name}")
            best_x = initial_vector
        update_dict(idx, result_dict, best_x, bounds, lower_bound_vector, upper_bound_vector)
        
    return result_dict
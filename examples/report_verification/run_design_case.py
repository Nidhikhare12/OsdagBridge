"""Run a reproducible verification bridge through the unmodified design engine."""
import os
import sys
from pathlib import Path
import pickle

if os.name == 'nt':
    handles = [os.add_dll_directory(str(Path(sys.prefix) / d))
               for d in ('Library/bin', 'DLLs') if (Path(sys.prefix) / d).is_dir()]
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT, solve_extend_basic_input_dict
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge

if __name__ == '__main__':
    inputs = dict(BASIC_INPUT_DICT)
    inputs.update({KEY_SPAN: 20.0, KEY_CARRIAGEWAY_WIDTH: 7.5, KEY_SKEW_ANGLE: 0.0,
                   KEY_DESIGN_MODE: 'Custom',
                   KEY_PROJECT_LOCATION: {'method': 'custom_data', 'data': {},
                                          'weather_data': {'wind_speed': 39, 'zone': 'II',
                                                           'max_temp': 40, 'min_temp': 10}}})
    solve_extend_basic_input_dict(inputs)
    from osdagbridge.desktop.ui.dialogs.material_properties import STEEL_MATERIAL_BASE_VALUES, CONCRETE_GRADE_BASE_VALUES
    steel = STEEL_MATERIAL_BASE_VALUES[''.join(inputs[KEY_GIRDER].upper().split())]
    for key, field in [(KEY_MATERIAL_GIRDER_FY, 'Fy'), (KEY_MATERIAL_GIRDER_FU, 'Fu'),
                       (KEY_MATERIAL_GIRDER_E, 'E'), (KEY_MATERIAL_GIRDER_G, 'G'),
                       (KEY_MATERIAL_GIRDER_POISSON, 'Poisson')]:
        inputs[key] = steel[field]
    deck = CONCRETE_GRADE_BASE_VALUES[inputs[KEY_DECK_CONCRETE_GRADE_BASIC].strip().upper()]
    for key, field in [(KEY_MATERIAL_DECK_FCK, 'fck'), (KEY_MATERIAL_DECK_FCTM, 'fctm'), (KEY_MATERIAL_DECK_ECM, 'Ecm')]:
        inputs[key] = deck[field]
    bridge = PlateGirderBridge()
    bridge.set_input(inputs)
    print('Starting 20 m verification bridge design', flush=True)
    bridge.design()
    with (Path(__file__).parent / 'design_case.pkl').open('wb') as stream:
        pickle.dump({'inputs': dict(bridge.input_dict), 'outputs': dict(bridge.output_dict)}, stream)
    print('COMPLETE: saved actual design output', flush=True)

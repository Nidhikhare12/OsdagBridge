import sys
sys.path.insert(0, '/Users/yuvraj/Documents/OsdagBridge/src')
print('BEGIN IMPORT')
try:
    import importlib
    importlib.import_module('osdagbridge.desktop.__main__')
    print('IMPORT SUCCEEDED')
except Exception as e:
    import traceback
    traceback.print_exc()

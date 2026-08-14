import sys
sys.path.insert(0, 'src')

def try_import(name):
    try:
        __import__(name)
        print(f"{name} OK")
        return True
    except Exception as e:
        print(f"{name} ERROR: {e}")
        return False

try_import('yaml')
try_import('osdag')
# Try importing osdag.cli
try:
    import importlib
    importlib.import_module('osdag.cli')
    print('osdag.cli OK')
except Exception as e:
    print('osdag.cli ERROR:', e)

try_import('osdag.design_type.compression_member.compression_bolted')

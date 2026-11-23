"""Patch bridge_ifc_generator.py to accept substructure_parts and add it to the IFC.

Usage (PowerShell, from the project root):
    python patch_bridge_ifc.py
Optional: pass the path to bridge_ifc_generator.py as the first argument.
"""
import ast
import pathlib
import sys

DEFAULT = (r"C:\Drive C\fosse\porject 2\OsdagBridge\src\osdagbridge"
           r"\core\ifc_export_bridge\bridge_ifc_generator.py")

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
if not path.exists():
    sys.exit(f"File not found: {path}")

text = path.read_bytes().decode("utf-8")
nl = "\r\n" if "\r\n" in text else "\n"

if "substructure_parts" in text:
    sys.exit("Already patched. Nothing to do.")

# Edit 1: new argument
old_sig = "def generate_from_extracted_data(self, extracted_dict, cad_context=None):"
new_sig = ("def generate_from_extracted_data(self, extracted_dict, cad_context=None, "
           "substructure_parts=None):")
if old_sig not in text:
    sys.exit("Could not find generate_from_extracted_data signature. No changes made.")
text = text.replace(old_sig, new_sig, 1)

# Edit 2: add substructure before the final print/save
marker = '# Intentionally ignore "deck_textures"'
idx = text.find(marker)
if idx == -1:
    sys.exit("Could not find the deck_textures comment. No changes made.")
line_start = text.rfind("\n", 0, idx) + 1
indent = text[line_start:idx]
block = nl.join([
    indent + "if substructure_parts:",
    indent + "    from osdagbridge.core.ifc_export_bridge.substructure_ifc import add_substructure_to_ifc",
    indent + "    add_substructure_to_ifc(self, substructure_parts, scale=0.001)",
    "",
])
text = text[:line_start] + block + text[line_start:]

# Check the result is valid Python before saving
try:
    ast.parse(text)
except SyntaxError as e:
    sys.exit(f"Patched text would have a syntax error ({e}). No changes made.")

path.write_bytes(text.encode("utf-8"))
print("Patched OK:", path)
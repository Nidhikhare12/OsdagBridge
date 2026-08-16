# styles.py - Centralized Style Configuration Module (Single Source of Truth)

# 1. Global Page Layout Parameters
GLOBAL_GEOMETRY = {
    "margin": "1in",
    "top": "1in",
    "bottom": "1.4in",
    "footskip": "0.4in"
}

# 2. Engineering Document Color Palette (Hex Codes)
COLOR_PALETTE = {
    "primary": "#1A365D",     # Deep Navy for structural headers
    "secondary": "#2B6CB0",   # Steel Blue for subsections
    "success": "#5CB85C",     # Passing checks (Green)
    "danger": "#D9534F",      # Failing checks (Red)
    "table_bg": "#F7FAFC"     # Soft light grey for alternating rows
}

# 3. Dynamic Table Grid Configurations
TABLE_STYLING = {
    "cell_padding": "6pt",
    "array_stretch": "1.25",   # Multi-page safety spacing factor
    "border_thickness": "0.5pt"
}

# 4. Typography Matrix
FONT_SETTINGS = {
    "document_font": "ptm",    # Standard Times New Roman core encoding
    "base_size": "11pt",
    "heading_size": "14pt"
}
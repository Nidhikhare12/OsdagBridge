# =============================================================================
# OsdagBridge Report Styles — Single Source of Truth
# =============================================================================
"""Single source of truth for report styling.

Every colour, margin, font size and table-padding value used by the report is
defined here. Chapter modules must not define their own.

This module provides:
- Constants for page geometry, fonts, colors, table spacing, header/footer rules
- Helper functions that return LaTeX code blocks (geometry, color definitions, etc.)
- Token-based template replacement (to avoid f-string brace conflicts)
"""

# =============================================================================
# Page Layout
# =============================================================================

PAGE = {
    "paper": "a4paper",
    "margin": "1in",
    "footskip": "40pt",      # Increased from default to prevent footer overlap (R2)
    "headheight": "15pt",    # Sufficient for 12pt header text
}

FONT_SIZE_PT = 12
LINE_STRETCH = 1.15

# =============================================================================
# Colors (HTML hex codes)
# =============================================================================

COLORS = {
    "osdagGreen": "91B014",
    "urFail": "C62828",       # Red for failing checks (UR > 1.0)
    "urPass": "91B014",       # Green for passing checks
    "urNA": "9E9E9E",         # Grey for N/A / missing data
}

# =============================================================================
# Table Layout
# =============================================================================

TABLE = {
    "tabcolsep": "6pt",              # Standard column padding
    "tabcolsep_compact": "3.5pt",    # Compact tables (chap7, chap8)
    "tabcolsep_tight": "4pt",        # Tight multi-column tables (chap2, chap5 CB tables)
    "arraystretch": 1.12,            # Standard row height multiplier
    "arraystretch_tall": 1.25,       # Tall rows (chap4 analysis tables)
    "rule_width": "0.5pt",           # Table border thickness
    "extrarowheight": "0.6pt",       # Extra space above row content
    "row_gap": "6pt",                # Vertical gap after row (\\[6pt])
    "lt_pre": "0pt",                 # Space before longtable
    "lt_post": "6pt",                # Space after longtable
    "needspace_lines": 5,            # Min lines needed before table starts
}

# =============================================================================
# Header and Footer
# =============================================================================

HEADER_FOOTER = {
    "rule_color": "osdagGreen",
    "rule_pt": 1,
}

# =============================================================================
# Chart Settings (for matplotlib-generated figures)
# =============================================================================

CHART = {
    "dpi": 200,
    "width_in": 6.2,            # Max width to fit A4 text block
    "height_in_max": 7.0,       # Max height to avoid large gaps
    "font_pt": 8,               # Minimum readable font size
    "ur_limit": 1.0,            # Red dashed line at UR = 1.0
    "limit_color": "#C62828",   # Red (matches urFail)
    "pass_color": "#91B014",    # Green (matches osdagGreen)
    "fail_color": "#C62828",    # Red
    "na_color": "#9E9E9E",      # Grey
}

# =============================================================================
# Helper Functions — LaTeX Code Generation
# =============================================================================

def latex_color_defs() -> str:
    """Return \\definecolor lines for all colors in COLORS."""
    lines = []
    for name, hex_code in COLORS.items():
        lines.append(f"\\definecolor{{{name}}}{{HTML}}{{{hex_code}}}")
    return "\n".join(lines)


def latex_table_settings() -> str:
    """Return \\setlength and \\renewcommand blocks for TABLE settings."""
    t = TABLE
    return f"""% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\\setlength{{\\tabcolsep}}{{{t["tabcolsep"]}}}
\\renewcommand{{\\arraystretch}}{{{t["arraystretch"]}}}
\\setlength{{\\LTpre}}{{{t["lt_pre"]}}}
\\setlength{{\\LTpost}}{{{t["lt_post"]}}}
% Table rules (outline thickness) and small extra row height for clarity
\\setlength{{\\arrayrulewidth}}{{{t["rule_width"]}}}
\\setlength{{\\extrarowheight}}{{{t["extrarowheight"]}}}

% Prevent tables from overflowing past the page bottom:
% if fewer than {t["needspace_lines"]} baseline-skips remain, break to the next page first.
\\BeforeBeginEnvironment{{table}}{{\\needspace{{{t["needspace_lines"]}\\baselineskip}}}}
\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{t["needspace_lines"]}\\baselineskip}}}}"""


def latex_geometry() -> str:
    """Return \\usepackage[...]{geometry} line with PAGE settings."""
    p = PAGE
    return f"\\usepackage[{p['paper']}, margin={p['margin']}, headheight={p['headheight']}, footskip={p['footskip']}]{{geometry}}"


def compact_table_begin() -> str:
    """Return LaTeX to temporarily set compact table spacing (chap7, chap8)."""
    return f"\\begingroup\n\\setlength{{\\tabcolsep}}{{{TABLE['tabcolsep_compact']}}}"


def compact_table_end() -> str:
    """Return LaTeX to restore default table spacing."""
    return "\\endgroup"


def tight_table_spacing() -> str:
    """Return LaTeX to set tight spacing for multi-column tables (chap2, chap5 CB)."""
    return f"\\setlength{{\\tabcolsep}}{{{TABLE['tabcolsep_tight']}}}"


def tall_row_stretch() -> str:
    """Return LaTeX to set tall row stretch for analysis tables (chap4)."""
    return f"\\renewcommand{{\\arraystretch}}{{{TABLE['arraystretch_tall']}}}"


# =============================================================================
# Preamble Template Tokens
# =============================================================================

def get_preamble_tokens() -> dict:
    """Return a dict of tokens for preamble template replacement.
    
    Usage in report_generator.py:
        tokens = styles.get_preamble_tokens()
        preamble_template = r"... @@GEOMETRY@@ ... @@COLORS@@ ..."
        for key, val in tokens.items():
            preamble_template = preamble_template.replace(f"@@{key}@@", val)
    """
    return {
        "GEOMETRY": latex_geometry(),
        "COLORS": latex_color_defs(),
        "TABLE_SETTINGS": latex_table_settings(),
        "FONT_SIZE": str(FONT_SIZE_PT),
        "LINE_STRETCH": str(LINE_STRETCH),
        "HEADER_RULE_COLOR": HEADER_FOOTER["rule_color"],
        "HEADER_RULE_PT": str(HEADER_FOOTER["rule_pt"]),
    }


# =============================================================================
# Color Name Accessors (for use in chapter files)
# =============================================================================

def color_fail() -> str:
    """Return LaTeX color name for failing checks."""
    return COLORS.get("urFail", "red")


def color_pass() -> str:
    """Return LaTeX color name for passing checks."""
    return COLORS.get("urPass", "black")


def color_na() -> str:
    """Return LaTeX color name for N/A / missing data."""
    return COLORS.get("urNA", "gray")

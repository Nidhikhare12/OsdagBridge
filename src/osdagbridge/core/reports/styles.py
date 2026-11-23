# =============================================================================
# OsdagBridge — Report Styles  (SINGLE SOURCE OF TRUTH)
# =============================================================================
#
# Every visual / layout decision of the PDF design report lives in this module:
#
#   1. COLORS          – one palette, used by LaTeX (xcolor) AND matplotlib
#   2. PAGE            – paper, margins, header/footer geometry, fonts
#   3. TABLE           – padding, rules, header fill, caption behaviour
#   4. TABLE_LAYOUTS   – named column layouts (alignment + width fraction)
#   5. FIGURE          – default widths / spacing of embedded figures
#   6. CHART           – matplotlib style for the UR and quantity charts
#   7. build_preamble()/title-page helpers – the LaTeX preamble, generated
#      from the constants above (nothing is hard-coded in the chapter files)
#
# Chapter files (chap1.py … chap9.py, executive_summary.py) and the helper
# modules (latex_tables.py, charts.py) must ONLY import from here — to change
# the look of the whole report, edit this file and nothing else.
# =============================================================================

from __future__ import annotations

# -----------------------------------------------------------------------------
# 1. COLOR PALETTE   (hex WITHOUT '#', as xcolor's HTML model expects)
# -----------------------------------------------------------------------------
COLORS = {
    "osdagGreen":      "91B014",   # brand colour: rules, headings, links
    "osdagGreenDark":  "5F7A0A",   # darker accent: chapter titles, chart bars
    "osdagGreenLight": "EAF1CC",   # table header fill
    "rowAlt":          "F7F9EE",   # alternate / group-label fill
    "ruleGrey":        "9A9A9A",   # table grid
    "textDark":        "1F1F1F",   # body text
    "noteGrey":        "555555",   # notes / captions
    "placeholderFill": "F2F2F2",   # figure placeholder background
    "passGreen":       "1B7F3B",   # PASS text
    "failRed":         "C62828",   # FAIL text / UR > 1
    "warnAmber":       "B26A00",   # warnings
}


def hex_color(name: str, with_hash: bool = True) -> str:
    """Return palette colour *name* as '#RRGGBB' (matplotlib) or 'RRGGBB'."""
    h = COLORS[name]
    return ("#" + h) if with_hash else h


# -----------------------------------------------------------------------------
# 2. PAGE / DOCUMENT
# -----------------------------------------------------------------------------
PAGE = {
    "document_class": "report",
    "font_size":      "11pt",
    "paper":          "a4paper",
    # geometry — bottom/footskip leave a guaranteed clear band above the footer
    "left":           "2.5cm",
    "right":          "2.5cm",
    "top":            "2.9cm",
    "bottom":         "3.0cm",
    "headheight":     "15pt",
    "headsep":        "0.9cm",
    "footskip":       "1.35cm",
    "line_stretch":   "1.12",       # \setstretch
    "text_width_cm":  16.0,         # = 21.0 - left - right (informational)
    "header_rule":    "0.9pt",
    "footer_rule":    "0.9pt",
}

FONT = {
    # Optional packages are loaded ONLY if they exist in the bundled TeX
    # distribution (\IfFileExists), so a minimal TeX install never breaks.
    "optional_packages": [],
    "footer_size":       r"\small",
    "note_size":         r"\footnotesize",
    "chapter_size":      r"\LARGE",
    "section_size":      r"\Large",
    "subsection_size":   r"\large",
}

HEADER_FOOTER = {
    "footer_left":  r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay",
    "footer_right": r"Page \thepage\ of \pageref{LastPage}",
    "software_default_note": r"* Software default value",
}

# -----------------------------------------------------------------------------
# 3. TABLES
# -----------------------------------------------------------------------------
TABLE = {
    "tabcolsep":        "4.5pt",    # horizontal cell padding
    "arraystretch":     "1.32",     # vertical cell padding (row height factor)
    "rule_width":       "0.4pt",
    "header_fill":      "osdagGreenLight",
    "header_text":      "textDark",
    "group_fill":       "rowAlt",
    "table_font":       r"\small",
    "keep_before":      r"8\baselineskip",   # \needspace before every table
    "lt_pre":           "4pt",
    "lt_post":          "8pt",
    "continued_suffix": r" (continued)",
    "continued_footer": r"\textit{Continued on next page}",
    "chunk_size":       100,        # \LTchunksize — rows per longtable chunk
}

# Named column layouts.  Each entry = list of (alignment, width fraction of
# \textwidth).  Alignment: L left, C centre, R right.  Fractions of a layout
# should sum to ~1.0; column text width is derived automatically, so tables
# can never overflow the page margins.
TABLE_LAYOUTS = {
    # generic
    "param_value":        [("L", 0.40), ("L", 0.60)],
    "param_value_note":   [("L", 0.38), ("L", 0.62)],
    "four_col_status":    [("L", 0.34), ("C", 0.22), ("C", 0.30), ("C", 0.14)],
    "three_col_status":   [("L", 0.44), ("L", 0.42), ("C", 0.14)],
    "code_year_scope":    [("C", 0.16), ("C", 0.10), ("L", 0.74)],
    # exec summary
    "exec_geometry":      [("C", 0.10), ("C", 0.14), ("C", 0.30), ("C", 0.30), ("C", 0.16)],
    # chapter 2
    "girder_general":     [("C", 0.12), ("C", 0.16), ("C", 0.24), ("C", 0.26), ("C", 0.22)],
    "girder_dims":        [("C", 0.09), ("C", 0.17), ("C", 0.14), ("C", 0.30), ("C", 0.30)],
    "girder_restraint":   [("C", 0.08), ("C", 0.17), ("C", 0.13), ("C", 0.24), ("C", 0.15), ("C", 0.23)],
    "bracing_members":    [("C", 0.16), ("C", 0.22), ("C", 0.22), ("C", 0.24), ("C", 0.16)],
    "diaphragm_members":  [("C", 0.18), ("C", 0.26), ("C", 0.28), ("C", 0.28)],
    # chapter 3
    "load_combos":       [("C", 0.14), ("L", 0.86)],
    "live_vehicle":       [("L", 0.24), ("C", 0.16), ("C", 0.14), ("C", 0.14), ("C", 0.14), ("C", 0.18)],
    "live_footpath":      [("L", 0.40), ("C", 0.22), ("L", 0.38)],
    # chapter 4
    "analysis_summary":   [("C", 0.215), ("C", 0.105), ("C", 0.075), ("C", 0.08), ("C", 0.105),
                           ("C", 0.075), ("C", 0.08), ("C", 0.13), ("C", 0.135)],
    "reactions":          [("L", 0.46), ("C", 0.27), ("C", 0.27)],
    # chapter 5 — grouped per girder (first column = girder label, multirow)
    "g_property":         [("C", 0.14), ("L", 0.52), ("C", 0.34)],
    "g_classification":   [("C", 0.14), ("L", 0.22), ("C", 0.24), ("C", 0.18), ("C", 0.22)],
    "g_check":            [("C", 0.10), ("L", 0.29), ("C", 0.25), ("C", 0.23), ("C", 0.13)],
    "g_stiffener_sum":    [("C", 0.14), ("L", 0.46), ("C", 0.40)],
    "g_stiffener_chk":    [("C", 0.10), ("L", 0.26), ("C", 0.20), ("C", 0.26), ("C", 0.18)],
    "g_service":          [("C", 0.10), ("L", 0.28), ("C", 0.22), ("C", 0.24), ("C", 0.16)],
    "g_fatigue":          [("C", 0.10), ("C", 0.25), ("C", 0.25), ("C", 0.22), ("C", 0.18)],
    "g_summary":          [("C", 0.09), ("C", 0.22), ("C", 0.18), ("C", 0.14), ("C", 0.14), ("C", 0.12), ("C", 0.11)],
    "sc_capacity":        [("L", 0.20), ("C", 0.36), ("C", 0.17), ("L", 0.27)],
    "sc_spacing":         [("L", 0.26), ("C", 0.28), ("C", 0.28), ("C", 0.18)],
    "trans_shear":        [("L", 0.38), ("L", 0.48), ("C", 0.14)],
    "deck_flexure":       [("C", 0.17), ("L", 0.26), ("C", 0.22), ("C", 0.22), ("C", 0.13)],
    "deck_check4":        [("L", 0.34), ("C", 0.22), ("C", 0.28), ("C", 0.16)],
    "deck_detailing":     [("L", 0.34), ("C", 0.25), ("C", 0.25), ("C", 0.16)],
    "deck_two_col":       [("L", 0.46), ("L", 0.54)],
    "tm_properties":      [("C", 0.13), ("L", 0.19), ("L", 0.17), ("C", 0.19), ("C", 0.16), ("C", 0.16)],
    "tm_slenderness":     [("C", 0.13), ("L", 0.19), ("C", 0.13), ("C", 0.19), ("C", 0.16), ("C", 0.20)],
    "tm_capacity":        [("C", 0.11), ("L", 0.11), ("C", 0.13), ("C", 0.22), ("C", 0.11), ("C", 0.12), ("C", 0.09), ("C", 0.11)],
    "overall_summary":    [("L", 0.22), ("L", 0.30), ("C", 0.17), ("C", 0.17), ("C", 0.14)],
    # chapter 7
    "bom":                [("C", 0.06), ("L", 0.19), ("C", 0.25), ("C", 0.10), ("C", 0.12), ("C", 0.13), ("C", 0.15)],
}

# -----------------------------------------------------------------------------
# 4. STATUS TOKENS  (PASS / FAIL cells)
# -----------------------------------------------------------------------------
STATUS = {
    "pass_text": "PASS",
    "fail_text": "FAIL",
    "na_text":   "---",
    "ur_limit":  1.0,           # UR <= limit  -> pass
}

# -----------------------------------------------------------------------------
# 5. FIGURES (LaTeX side)
# -----------------------------------------------------------------------------
FIGURE = {
    "default_width":    r"0.86\textwidth",
    "chart_width":      r"0.90\textwidth",
    "wide_width":       r"0.95\textwidth",
    "small_width":      r"0.75\textwidth",
    "placement":        "H",
    "caption_font":     "small",
    "placeholder_text": "PLACEHOLDER",
}

# -----------------------------------------------------------------------------
# 6. CHARTS (matplotlib side — used by charts.py)
# -----------------------------------------------------------------------------
CHART = {
    "dpi":              220,
    "font_family":      "DejaVu Sans",
    "title_size":       12.5,
    "label_size":       10.5,
    "tick_size":        9.5,
    "value_label_size": 9.5,
    "bar_width":        0.62,
    "grid_alpha":       0.25,
    # utilization-ratio charts
    "ur_overall_size":  (8.2, 4.6),
    "ur_detail_size":   (8.2, 3.6),
    "ur_pass_color":    hex_color("osdagGreen"),
    "ur_fail_color":    hex_color("failRed"),
    "ur_threshold":     {"value": 1.0, "color": "#D32F2F", "linestyle": "--", "linewidth": 1.8,
                         "label": "Limit  UR = 1.0"},
    "ur_headroom":      1.18,   # y-axis headroom over the tallest bar / limit
    # quantity charts
    "qty_size":         (8.2, 4.0),
    "qty_colors":       ["#4C6A92", "#91B014", "#E0A030", "#B05A7A", "#5A9E9E"],
    "concrete_color":   "#8A8D91",
    "rebar_color":      "#B5651D",
}

# -----------------------------------------------------------------------------
# 7. LATEX BUILDERS  (preamble / title-page fragments from the constants above)
# -----------------------------------------------------------------------------

def _color_definitions() -> str:
    return "\n".join(
        r"\definecolor{%s}{HTML}{%s}" % (name, hexv) for name, hexv in COLORS.items()
    )


def _optional_packages() -> str:
    return "\n".join(
        r"\IfFileExists{%s.sty}{\usepackage{%s}}{}" % (p, p) for p in FONT["optional_packages"]
    )


def header_footer_tex(project_name: str, job_number: str, report_date: str,
                      report_version: str) -> str:
    """fancyhdr page styles.  Arguments must already be LaTeX-escaped."""
    left = project_name + (r" $|$ " + job_number if job_number else "")
    right = report_date + (r" $|$ " + report_version if report_version else "")
    hf, p = HEADER_FOOTER, PAGE

    def _style(name: str, with_header: bool = True) -> str:
        head = (
            r"  \fancyhead[L]{" + left + "}\n"
            r"  \fancyhead[R]{" + right + "}\n"
            r"  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height " + p["header_rule"] + r"}"
            if with_header else
            r"  \renewcommand{\headrulewidth}{0pt}"
        )
        return (
            r"\fancypagestyle{" + name + "}{\n"
            r"  \fancyhf{}" + "\n"
            + head + "\n"
            r"  \fancyfoot[L]{" + FONT["footer_size"] + " " + hf["footer_left"] + "}\n"
            r"  \fancyfoot[R]{" + FONT["footer_size"] + " " + hf["footer_right"] + "}\n"
            # Footer layout: (optional) software-default note on its own line
            # ABOVE the rule, rule, then footer text.  Everything lives inside
            # the \footskip band, so body text can never collide with it.
            r"  \renewcommand{\footrule}{%" + "\n"
            r"    \ifbool{hasSDonPage}{%" + "\n"
            r"      \hbox to \headwidth{{" + FONT["note_size"] + r"\color{noteGrey}\textit{" + hf["software_default_note"] + r"}}\hfil}\vspace{3pt}%" + "\n"
            r"    }{}%" + "\n"
            r"    {\color{osdagGreen}\hrule width\headwidth height " + p["footer_rule"] + r"}\vspace{4pt}%" + "\n"
            r"  }" + "\n"
            "}\n"
        )

    return _style("main") + _style("plain") + _style("firstpage", with_header=False)


def build_preamble(project_name: str, job_number: str, report_date: str,
                   report_version: str = "Rev 0") -> str:
    """Full LaTeX preamble (documentclass … \\begin{document}).

    All four arguments must already be LaTeX-escaped (see report_utils._tex).
    """
    p, t = PAGE, TABLE
    tpl = r"""
\documentclass[@@font_size@@,@@paper@@]{@@document_class@@}

% ── Page geometry ───────────────────────────────────────────────────────────
\usepackage[@@paper@@, left=@@left@@, right=@@right@@, top=@@top@@, bottom=@@bottom@@,
            headheight=@@headheight@@, headsep=@@headsep@@, footskip=@@footskip@@]{geometry}

% ── Core packages (all already part of the Osdag LaTeX bundle) ──────────────
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage[table]{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
@@optional_packages@@

% ── Colour palette (from styles.COLORS) ─────────────────────────────────────
@@colors@@

% ── Captions ────────────────────────────────────────────────────────────────
\captionsetup{
    labelfont={bf,color=osdagGreenDark},
    textfont=bf,
    labelsep=colon,
    justification=raggedright,
    singlelinecheck=false,
    format=plain,
    skip=4pt
}
\captionsetup[figure]{position=bottom, textfont=normalfont, font=@@caption_font@@, skip=6pt}
\captionsetup[table]{position=top}
\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}

% ── Table style (from styles.TABLE) ─────────────────────────────────────────
\setlength{\tabcolsep}{@@tabcolsep@@}
\renewcommand{\arraystretch}{@@arraystretch@@}
\setlength{\arrayrulewidth}{@@rule_width@@}
\arrayrulecolor{ruleGrey}
\setlength{\LTpre}{@@lt_pre@@}
\setlength{\LTpost}{@@lt_post@@}
\setlength{\LTleft}{0pt}
\setlength{\LTright}{0pt}
\setlength{\LTcapwidth}{\textwidth}
\LTchunksize=@@chunk_size@@
\setlength{\hfuzz}{2pt}
\setlength{\emergencystretch}{2em}

% Never start a float-table in the last few lines of a page.  (longtable is NOT
% guarded: it already keeps its header together with the first rows, and an
% extra \needspace made it emit a duplicate "continued" caption.)
\BeforeBeginEnvironment{table}{\needspace{@@keep_before@@}}

% ── Header / footer ─────────────────────────────────────────────────────────
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\newcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

@@header_footer@@
\pagestyle{main}
\setstretch{@@line_stretch@@}
\raggedbottom

% ── Custom commands ─────────────────────────────────────────────────────────
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcommand{\passtxt}{\textcolor{passGreen}{\textbf{@@pass_text@@}}}
\newcommand{\failtxt}{\textcolor{failRed}{\textbf{@@fail_text@@}}}
\newcommand{\hcell}[1]{\textbf{#1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}m{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}m{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}m{#1}}
\newcommand{\hdrfill}{\rowcolor{@@header_fill@@}}
\newcommand{\grpfill}{\rowcolor{@@group_fill@@}}

% ── Headings ────────────────────────────────────────────────────────────────
\titleformat{\chapter}[block]
  {\normalfont@@chapter_size@@\bfseries\color{osdagGreenDark}}
  {\thechapter}{0.8em}{}[\vspace{2pt}{\color{osdagGreen}\titlerule[1.2pt]}]
\titlespacing*{\chapter}{0pt}{-10pt}{14pt}
\titleformat{\section}
  {\normalfont@@section_size@@\bfseries\color{osdagGreenDark}}{\thesection}{0.7em}{}
\titlespacing*{\section}{0pt}{14pt}{6pt}
\titleformat{\subsection}
  {\normalfont@@subsection_size@@\bfseries}{\thesubsection}{0.7em}{}
\titlespacing*{\subsection}{0pt}{10pt}{4pt}
\setlist[itemize]{leftmargin=1.6em, itemsep=2pt, topsep=4pt}
\setlist[enumerate]{leftmargin=1.8em, itemsep=3pt, topsep=4pt}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    values = {
        **p, **t,
        "optional_packages": _optional_packages(),
        "colors": _color_definitions(),
        "caption_font": FIGURE["caption_font"],
        "header_footer": header_footer_tex(project_name, job_number, report_date, report_version),
        "pass_text": STATUS["pass_text"],
        "fail_text": STATUS["fail_text"],
        "chapter_size": FONT["chapter_size"],
        "section_size": FONT["section_size"],
        "subsection_size": FONT["subsection_size"],
    }
    for key, val in values.items():
        tpl = tpl.replace("@@" + key + "@@", str(val))
    return tpl


def toc_tex() -> str:
    """Table-of-contents block (heading style + entry formatting)."""
    return r"""
% TOC styling
\setcounter{tocdepth}{2}
\titlecontents{chapter}[1.5em]
  {\normalfont\bfseries\vspace{3pt}}
  {\contentslabel{1.5em}}
  {\hspace*{-1.5em}}
  {\titlerule*[0.6pc]{.}\contentspage}
\titlecontents{section}[3.8em]
  {\normalfont}
  {\contentslabel{2.3em}}
  {\hspace*{-2.3em}}
  {\titlerule*[0.6pc]{.}\contentspage}
\titlecontents{subsection}[7.0em]
  {\normalfont\small}
  {\contentslabel{3.2em}}
  {\hspace*{-3.2em}}
  {\titlerule*[0.6pc]{.}\contentspage}

\clearpage
\begingroup
\titleformat{\chapter}[block]{\normalfont\LARGE\bfseries\color{osdagGreenDark}\centering}{}{0pt}{}[\vspace{2pt}{\color{osdagGreen}\titlerule[1.2pt]}]
\renewcommand{\contentsname}{Table of Contents}
\tableofcontents
\endgroup
"""


def front_heading(title: str) -> str:
    """Unnumbered, centred heading used for 'Executive Summary' / 'References'."""
    return (
        r"\clearpage" + "\n"
        r"\begingroup" + "\n"
        r"\titleformat{\chapter}[block]{\normalfont\LARGE\bfseries\color{osdagGreenDark}}{}{0pt}{}"
        r"[\vspace{2pt}{\color{osdagGreen}\titlerule[1.2pt]}]" + "\n"
        r"\chapter*{" + title + "}\n"
        r"\addcontentsline{toc}{chapter}{" + title + "}\n"
        r"\endgroup" + "\n"
    )

# =============================================================================
# OsdagBridge report styling — single source of truth for LaTeX geometry,
# colours, table metrics, preamble, and repeating longtable headers.
# Chapter modules must import helpers from here instead of inlining
# \\setlength / \\vspace / \\textcolor for layout.
# =============================================================================

from osdagbridge.core.reports.report_utils import _tex

# --- Page geometry (A4). Bottom + footskip are sized so fancyhdr never
#     collides with longtable rows (the previous 1in-all-around layout
#     left the green footer rule overlapping the last table rows). ---
PAPER = "a4paper"
FONT_SIZE = "12pt"
MARGIN_TOP = "1.00in"
MARGIN_LEFT = "1.00in"
MARGIN_RIGHT = "1.00in"
MARGIN_BOTTOM = "1.30in"
HEADHEIGHT = "16pt"
HEADSEP = "14pt"
FOOTSKIP = "42pt"

# --- Table metrics ---
TABCOLSEP = "6pt"
TABCOLSEP_COMPACT = "3.5pt"
TABCOLSEP_DENSE = "3pt"
TABCOLSEP_BRACING = "4pt"
ARRAYSTRETCH = "1.12"
ARRAYSTRETCH_DENSE = "1.25"
ARRAYRULEWIDTH = "0.5pt"
EXTRAROWHEIGHT = "0.6pt"
LT_PRE = "0pt"
LT_POST = "10pt"
NEEDSPACE = r"8\baselineskip"
ROW_SKIP = r"\\[6pt]"
ROW_SKIP_WIDE = r"\\[8pt]"

# --- Vertical rhythm ---
VSPACE_TABLE = r"\vspace{1em}"
VSPACE_SMALL = r"\vspace{0.4em}"
VSPACE_SECTION = r"\vspace{0.8em}"
VSPACE_CAPTION = "2pt"
VSPACE_AFTER_TABLE = r"\vspace{0.4cm}"

# --- Colours ---
OSDAGE_GREEN_HEX = "91B014"
COLOR_OSDAGE = "osdagGreen"
COLOR_FAIL = "red"
COLOR_WARN = "blue"
COLOR_PASS = "black"
COLOR_TODO = "yellow"

# Matplotlib (charts.py) — keep in lockstep with the LaTeX brand colour.
MPL_PASS = "#91B014"
MPL_FAIL = "#C0392B"
MPL_THRESHOLD = "#C0392B"
MPL_NA = "#B0B0B0"
CHART_DPI = 200

# --- Column type helpers used in colspecs ---
COL_PARAM = r"|L{5.5cm}|p{10.0cm}|"
COL_PARAM_VALUE = r"|L{5.5cm}|L{8.5cm}|"
COL_TITLEPAGE = r"|L{4cm}|L{10cm}|"


def color_tex(name, text):
    """Wrap *text* in \\textcolor{name}{...}."""
    return rf"\textcolor{{{name}}}{{{text}}}"


def status_tex(ok, pass_label="PASS", fail_label="FAIL"):
    """PASS (black) / FAIL (red). *ok* is bool; None → '---'."""
    if ok is None:
        return "---"
    if ok:
        return pass_label
    return color_tex(COLOR_FAIL, fail_label)


def status_bands(ratio, pass_lt=0.90, warn_lt=1.00):
    """PASS / WARN / FAIL from a utilization ratio (engine bands)."""
    try:
        r = float(ratio)
    except (TypeError, ValueError):
        return "---"
    if r < pass_lt:
        return "PASS"
    if r < warn_lt:
        return "WARN"
    return color_tex(COLOR_FAIL, "FAIL")


def ur_tex(value, nd=2):
    """Format a utilization ratio; red when it exceeds 1.0."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    s = f"{f:.{nd}f}"
    return color_tex(COLOR_FAIL, s) if f > 1.0 else s


def log_line_tex(escaped, level):
    """Chapter 8 log colouring: WARNING=blue, ERROR=red, INFO=green."""
    lv = (level or "").upper()
    if "WARNING" in lv:
        return color_tex(COLOR_WARN, escaped) + r"\\"
    if "ERROR" in lv:
        return color_tex(COLOR_FAIL, escaped) + r"\\"
    if "INFO" in lv:
        return color_tex(COLOR_OSDAGE, escaped) + r"\\"
    return ""


def table_group(tabcolsep=None, arraystretch=None, footnotesize=False,
                lt_flush_left=False):
    """Return (open, close) LaTeX wrapping a local table metric override."""
    bits = [r"\begingroup"]
    if footnotesize:
        bits.append(r"\footnotesize")
    if tabcolsep:
        bits.append(rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}")
    if arraystretch:
        bits.append(rf"\renewcommand{{\arraystretch}}{{{arraystretch}}}")
    if lt_flush_left:
        bits.append(r"\setlength{\LTleft}{0pt}")
        bits.append(r"\setlength{\LTright}{\fill}")
    return "\n".join(bits) + "\n", r"\endgroup" + "\n"


def lt_begin(colspec, caption, header, *, continued=True):
    """Open a ``longtable`` with repeating caption + column headers.

    Parameters
    ----------
    colspec : str
        Column specification *without* the outer braces, e.g. ``|L{5.5cm}|p{10cm}|``.
    caption : str
        Caption text (already LaTeX-safe). Wrapped in ``\\textbf``.
    header : str
        Column-header row(s), including the trailing ``\\\\`` (and optional
        ``[6pt]``) but *not* the surrounding ``\\hline``.
    continued : bool
        If True, subsequent pages get ``Caption (continued)``.
    """
    cap = r"\textbf{" + caption + "}"
    cap_cont = cap + r" (continued)" if continued else cap
    hdr = header.strip()
    if not hdr.endswith(r"\\") and r"\\" not in hdr[-8:]:
        hdr = hdr + r" \\"
    return (
        r"\begin{longtable}{" + colspec + "}\n"
        r"\caption{" + cap + r"}\\" + "\n"
        r"\hline" + "\n"
        + hdr + "\n"
        r"\hline" + "\n"
        r"\endfirsthead" + "\n"
        r"\caption[]{" + cap_cont + r"}\\" + "\n"
        r"\hline" + "\n"
        + hdr + "\n"
        r"\hline" + "\n"
        r"\endhead" + "\n"
        r"\hline" + "\n"
        r"\endfoot" + "\n"
        r"\hline" + "\n"
        r"\endlastfoot" + "\n"
    )


def lt_end():
    return r"\end{longtable}"


def chapter_titleformat(after_skip="10pt", before_skip="0pt"):
    """titlesec chapter style used in the TOC block and after the exec summary."""
    return (
        r"\titleformat{\chapter}[block]"
        r"{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}" + "\n"
        rf"\titlespacing*{{\chapter}}{{0pt}}{{{before_skip}}}{{{after_skip}}}"
    )


def preamble(project_name, job_number, report_date, report_version="Rev 0"):
    """Full LaTeX preamble through ``\\begin{document}``."""
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    geometry = (
        rf"a4paper,"
        rf"top={MARGIN_TOP},bottom={MARGIN_BOTTOM},"
        rf"left={MARGIN_LEFT},right={MARGIN_RIGHT},"
        rf"headheight={HEADHEIGHT},headsep={HEADSEP},footskip={FOOTSKIP}"
    )
    header_l = pn + r" $|$ " + jn
    header_r = rd + r" $|$ " + rv
    footer_l = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
    return (
        rf"\documentclass[{FONT_SIZE},{PAPER}]{{report}}" + "\n\n"
        r"% Packages" + "\n"
        rf"\usepackage[{geometry}]{{geometry}}" + "\n"
        r"\usepackage{graphicx}" + "\n"
        r"\usepackage{amsmath}" + "\n"
        r"\usepackage{amssymb}" + "\n"
        r"\usepackage{booktabs}" + "\n"
        r"\usepackage{array}" + "\n"
        r"\usepackage{tabularx}" + "\n"
        r"\usepackage{float}" + "\n"
        r"\usepackage{fancyhdr}" + "\n"
        r"\usepackage[hidelinks]{hyperref}" + "\n"
        r"\usepackage{xcolor}" + "\n"
        r"\usepackage{setspace}" + "\n"
        r"\usepackage{enumitem}" + "\n"
        r"\usepackage{caption}" + "\n\n"
        r"\captionsetup{" + "\n"
        r"    labelfont=bf," + "\n"
        r"    justification=raggedright," + "\n"
        r"    singlelinecheck=false," + "\n"
        r"    format=plain," + "\n"
        rf"    skip={VSPACE_CAPTION}" + "\n"
        r"}" + "\n"
        r"\usepackage{subcaption}" + "\n"
        r"\usepackage{multirow}" + "\n"
        r"\usepackage{colortbl}" + "\n"
        r"\usepackage{longtable}" + "\n"
        r"\setlength{\LTleft}{\fill}" + "\n"
        r"\setlength{\LTright}{\fill}" + "\n"
        r"\setlength{\LTcapwidth}{\textwidth}" + "\n"
        r"\usepackage{titlesec}" + "\n"
        r"\usepackage{titletoc}" + "\n"
        r"\usepackage{lastpage}" + "\n"
        r"\usepackage{makecell}" + "\n"
        r"\usepackage{etoolbox}" + "\n"
        r"\usepackage{needspace}" + "\n\n"
        r"\numberwithin{table}{chapter}" + "\n"
        r"\numberwithin{figure}{chapter}" + "\n"
        rf"\setlength{{\tabcolsep}}{{{TABCOLSEP}}}" + "\n"
        rf"\renewcommand{{\arraystretch}}{{{ARRAYSTRETCH}}}" + "\n"
        rf"\setlength{{\LTpre}}{{{LT_PRE}}}" + "\n"
        rf"\setlength{{\LTpost}}{{{LT_POST}}}" + "\n"
        rf"\setlength{{\arrayrulewidth}}{{{ARRAYRULEWIDTH}}}" + "\n"
        rf"\setlength{{\extrarowheight}}{{{EXTRAROWHEIGHT}}}" + "\n\n"
        rf"\BeforeBeginEnvironment{{table}}{{\needspace{{{NEEDSPACE}}}}}" + "\n"
        rf"\BeforeBeginEnvironment{{longtable}}{{\needspace{{{NEEDSPACE}}}}}" + "\n\n"
        rf"\definecolor{{{COLOR_OSDAGE}}}{{HTML}}{{{OSDAGE_GREEN_HEX}}}" + "\n\n"
        + _fancyhdr("main", header_l, header_r, footer_l, with_head=True)
        + _fancyhdr("plain", header_l, header_r, footer_l, with_head=True)
        + _fancyhdr("firstpage", header_l, header_r, footer_l, with_head=False)
        + r"\pagestyle{main}" + "\n"
        r"\setstretch{1.15}" + "\n\n"
        r"\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}" + "\n"
        rf"\newcommand{{\todo}}[1]{{\colorbox{{{COLOR_TODO}}}{{TODO: #1}}}}" + "\n"
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}" + "\n"
        r"\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}" + "\n"
        r"\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}" + "\n\n"
        r"\newcommand{\sdstar}{\textsuperscript{*}}" + "\n"
        r"\newbool{hasSDonPage}" + "\n"
        r"\boolfalse{hasSDonPage}" + "\n"
        r"\newcommand{\markSD}{\global\booltrue{hasSDonPage}}" + "\n"
        r"\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}" + "\n"
        r"\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}" + "\n\n"
        r"\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software "
        r"for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}" + "\n"
        r"\author{}" + "\n"
        r"\date{}" + "\n\n"
        r"\begin{document}" + "\n"
    )


def _fancyhdr(name, header_l, header_r, footer_l, with_head):
    """One fancyhdr pagestyle. Extra room is reserved for the SD-asterisk note."""
    head = ""
    if with_head:
        head = (
            rf"  \fancyhead[L]{{{header_l}}}" + "\n"
            rf"  \fancyhead[R]{{{header_r}}}" + "\n"
            rf"  \renewcommand{{\headrule}}{{\color{{{COLOR_OSDAGE}}}"
            r"\hrule width\headwidth height 1pt \vspace{2pt}}" + "\n"
        )
    else:
        head = r"  \renewcommand{\headrulewidth}{0pt}" + "\n"
    # The SD note is typeset *above* the green rule, inside the footer box
    # (footskip is large enough that this never collides with body text).
    footrule = (
        r"  \renewcommand{\footrule}{%" + "\n"
        r"    \ifbool{hasSDonPage}{%" + "\n"
        r"      \vspace{2pt}%" + "\n"
        r"      \hbox to \headwidth{\textcolor{black}"
        r"{\footnotesize\textit{* Software default value}}\hfil}%" + "\n"
        r"      \vspace{4pt}%" + "\n"
        r"    }{%" + "\n"
        r"      \vspace{2pt}%" + "\n"
        r"    }%" + "\n"
        rf"    \color{{{COLOR_OSDAGE}}}\hrule width\headwidth height 1pt \vspace{{4pt}}%" + "\n"
        r"  }" + "\n"
    )
    if name == "firstpage":
        footrule = (
            rf"  \renewcommand{{\footrule}}{{\vspace{{2pt}}\color{{{COLOR_OSDAGE}}}"
            r"\hrule width\headwidth height 1pt \vspace{4pt}}" + "\n"
        )
    return (
        rf"\fancypagestyle{{{name}}}{{" + "\n"
        r"  \fancyhf{}" + "\n"
        + head
        + rf"  \fancyfoot[L]{{{footer_l}}}" + "\n"
        r"  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}" + "\n"
        + footrule
        + r"}" + "\n"
    )


def toc_section():
    """Numbered TOC page, using the shared chapter title format."""
    return (
        "% Chapter / TOC Formatting\n"
        + chapter_titleformat(after_skip="10pt", before_skip="0pt") + "\n"
        r"\setcounter{tocdepth}{2}" + "\n\n"
        r"\titlecontents{chapter}[1.5em]" + "\n"
        r"  {\normalfont\vspace{2pt}}" + "\n"
        r"  {\contentslabel{1.5em}}" + "\n"
        r"  {\hspace*{-1.5em}}" + "\n"
        r"  {\hfill\contentspage}" + "\n\n"
        r"\titlecontents{section}[3.8em]" + "\n"
        r"  {\normalfont}" + "\n"
        r"  {\contentslabel{2.3em}}" + "\n"
        r"  {\hspace*{-2.3em}}" + "\n"
        r"  {\hfill\contentspage}" + "\n\n"
        r"\titlecontents{subsection}[7.0em]" + "\n"
        r"  {\normalfont}" + "\n"
        r"  {\contentslabel{3.2em}}" + "\n"
        r"  {\hspace*{-3.2em}}" + "\n"
        r"  {\hfill\contentspage}" + "\n\n"
        r"\newpage" + "\n"
        r"\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}" + "\n"
        r"\tableofcontents" + "\n"
    )

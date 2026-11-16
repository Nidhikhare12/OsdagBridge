"""Document-level LaTeX structure builders (Preamble, Title Page, Table of Contents).

All lengths, colors, paddings, and font sizes are driven exclusively
by the centralized Theme system (Requirement R6).
"""

from osdagbridge.core.reports.latex.escape import tex
from osdagbridge.core.reports.theme import get_active_theme, Theme


def build_preamble(
    project_name: str,
    job_number: str,
    report_date: str,
    report_version: str = "Rev 0",
    theme: Theme | None = None,
) -> str:
    """Construct the LaTeX document preamble driven by the active theme."""
    t = theme or get_active_theme()
    p = t.page
    pal = t.palette
    tbl = t.table
    hf = t.header_footer

    raw_pn = str(project_name or "")
    if len(raw_pn) > hf.header_left_max_chars:
        raw_pn = raw_pn[: hf.header_left_max_chars - 1].rstrip() + "..."
    pn = tex(raw_pn)

    raw_jn = str(job_number or "")
    if len(raw_jn) > hf.header_job_max_chars:
        raw_jn = raw_jn[: hf.header_job_max_chars - 1].rstrip() + "..."
    jn = tex(raw_jn)

    raw_rd = str(report_date or "")
    if len(raw_rd) > hf.header_date_max_chars:
        raw_rd = raw_rd[: hf.header_date_max_chars - 1].rstrip() + "..."
    rd = tex(raw_rd)

    raw_rv = str(report_version or "")
    if len(raw_rv) > hf.footer_center_max_chars:
        raw_rv = raw_rv[: hf.footer_center_max_chars - 1].rstrip() + "..."
    rv = tex(raw_rv)

    return rf"""
\documentclass[{p.font_size_pt}pt,{p.paper}]{{report}}

% Packages
\usepackage[{p.paper}, top={p.margin_top_cm}cm, bottom={p.margin_bottom_cm}cm, left={p.margin_left_cm}cm, right={p.margin_right_cm}cm, headheight={p.head_height_pt}pt, headsep={p.head_sep_pt}pt, footskip={p.foot_skip_pt}pt]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{tabularx}}
\usepackage{{float}}
\usepackage{{fancyhdr}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{xcolor}}
\usepackage{{setspace}}
\usepackage{{enumitem}}
\usepackage{{caption}}

\captionsetup{{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}}
\usepackage{{subcaption}}
\usepackage{{multirow}}
\usepackage{{colortbl}}
\usepackage{{longtable}}
\setlength{{\LTleft}}{{0pt}}
\setlength{{\LTright}}{{\fill}}
\usepackage{{titlesec}}
\usepackage{{titletoc}}
\usepackage{{lastpage}}
\usepackage{{makecell}}
\usepackage{{etoolbox}}
\usepackage{{needspace}}

% Unicode symbols that reach the report inside engine-generated strings
\DeclareUnicodeCharacter{{2264}}{{\ensuremath{{\leq}}}}
\DeclareUnicodeCharacter{{2265}}{{\ensuremath{{\geq}}}}
\DeclareUnicodeCharacter{{00D7}}{{\ensuremath{{\times}}}}
\DeclareUnicodeCharacter{{00B5}}{{\ensuremath{{\mu}}}}
\DeclareUnicodeCharacter{{03C6}}{{\ensuremath{{\phi}}}}
\DeclareUnicodeCharacter{{2212}}{{\ensuremath{{-}}}}
\DeclareUnicodeCharacter{{2248}}{{\ensuremath{{\approx}}}}
\DeclareUnicodeCharacter{{2260}}{{\ensuremath{{\neq}}}}
\DeclareUnicodeCharacter{{00B1}}{{\ensuremath{{\pm}}}}

\numberwithin{{table}}{{chapter}}
\numberwithin{{figure}}{{chapter}}

% Table layout and spacing
\setlength{{\tabcolsep}}{{{tbl.col_sep_pt}pt}}
\renewcommand{{\arraystretch}}{{{tbl.row_stretch}}}
\setlength{{\LTpre}}{{0pt}}
\setlength{{\LTpost}}{{{tbl.row_pad_pt}pt}}
\setlength{{\arrayrulewidth}}{{{tbl.rule_width_pt}pt}}
\setlength{{\extrarowheight}}{{0.6pt}}

% Prevent tables from overflowing past page bottom
\BeforeBeginEnvironment{{table}}{{\needspace{{{tbl.min_rows_before_break}\baselineskip}}}}

\definecolor{{osdagBrand}}{{HTML}}{{{pal.brand}}}
\definecolor{{osdagRuleLight}}{{HTML}}{{{pal.rule_light}}}
\definecolor{{osdagPass}}{{HTML}}{{{pal.status_pass}}}
\definecolor{{osdagFail}}{{HTML}}{{{pal.status_fail}}}

\fancypagestyle{{main}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\footnotesize {pn}}}
  \fancyhead[R]{{\footnotesize {jn}\ \textperiodcentered\ {rd}}}
  \fancyfoot[L]{{\footnotesize {hf.footer_text}}}
  \fancyfoot[C]{{\footnotesize {rv}}}
  \fancyfoot[R]{{\footnotesize Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagBrand}}\hrule width\headwidth height {hf.rule_height_pt}pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \noindent\parbox[b]{{\headwidth}}{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}}}\par\vspace{{2pt}}%
    }}{{%
      \vspace{{{hf.sd_note_reserved_height_pt}pt}}%
    }}%
    \color{{osdagBrand}}\hrule width\headwidth height {hf.rule_height_pt}pt \vspace{{4pt}}%
  }}
}}

\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\footnotesize {pn}}}
  \fancyhead[R]{{\footnotesize {jn}\ \textperiodcentered\ {rd}}}
  \fancyfoot[L]{{\footnotesize {hf.footer_text}}}
  \fancyfoot[C]{{\footnotesize {rv}}}
  \fancyfoot[R]{{\footnotesize Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagBrand}}\hrule width\headwidth height {hf.rule_height_pt}pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \noindent\parbox[b]{{\headwidth}}{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}}}\par\vspace{{2pt}}%
    }}{{%
      \vspace{{{hf.sd_note_reserved_height_pt}pt}}%
    }}%
    \color{{osdagBrand}}\hrule width\headwidth height {hf.rule_height_pt}pt \vspace{{4pt}}%
  }}
}}

\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{{hf.footer_text}}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\footrule}}{{\vspace{{{hf.sd_note_reserved_height_pt}pt}}\color{{osdagBrand}}\hrule width\headwidth height {hf.rule_height_pt}pt \vspace{{4pt}}}}
}}

\pagestyle{{main}}
\setstretch{{{p.line_stretch}}}

% Column type aliases
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}

% Software-default asterisk marker
\newcommand{{\sdstar}}{{\textsuperscript{{*}}}}
\newbool{{hasSDonPage}}
\boolfalse{{hasSDonPage}}
\newcommand{{\markSD}}{{\global\booltrue{{hasSDonPage}}}}
\renewcommand{{\sdstar}}{{\textsuperscript{{*}}\markSD{{}}}}
\AddToHook{{shipout/before}}{{\global\boolfalse{{hasSDonPage}}}}

\title{{\Large\textbf{{OsdagBridge}} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{{2cm}} \large Design Report}}
\author{{}}
\date{{}}

\begin{{document}}
"""


def title_page(metadata, osdag_logo: str | None, org_logo: str | None, theme: Theme | None = None) -> str:
    """Generate the standardized Cover / Title page."""
    t = theme or get_active_theme()

    if osdag_logo:
        lhs = r"\includegraphics[width=\linewidth,keepaspectratio]{" + osdag_logo.replace("\\", "/") + r"}"
    else:
        lhs = r"\textit{(Osdag Logo)}"

    if org_logo:
        rhs = r"\includegraphics[width=\linewidth,height=2.2cm,keepaspectratio]{" + org_logo.replace("\\", "/") + r"}"
    else:
        rhs = ""

    logos_tex = rf"""\noindent
\begin{{minipage}}[c]{{0.6\textwidth}}
\raggedright
{lhs}
\end{{minipage}}%
\hfill
\begin{{minipage}}[c]{{0.35\textwidth}}
\raggedleft
{rhs}
\end{{minipage}}
"""

    return rf"""
\thispagestyle{{firstpage}}
\begin{{titlepage}}
{logos_tex}

\vspace{{2.5cm}}
\begin{{center}}
    {{\fontsize{{24}}{{28}}\selectfont\textbf{{OsdagBridge}}}}\\[0.4em]
    {{\large Open Source Software for Steel Girder Bridge Design}}\\[2.5em]
    {{\Large Design Report}}
\end{{center}}

\vspace{{2.5cm}}
\noindent
\begin{{table}}[h!]
\centering
\begin{{tabular}}{{|L{{4.5cm}}|L{{10.5cm}}|}}
\hline
\textbf{{Project Name}} & {tex(metadata.project_name)} \\[6pt]
\hline
\textbf{{Project Location}} & {tex(metadata.project_location)} \\[6pt]
\hline
\textbf{{Author / Designer}} & {tex(metadata.designer)} \\[6pt]
\hline
\textbf{{Reviewer}} & {tex(metadata.reviewer)} \\[6pt]
\hline
\textbf{{Organization}} & {tex(metadata.company)} \\[6pt]
\hline
\textbf{{Client Name and Organization}} & {tex(metadata.client)} \\[6pt]
\hline
\textbf{{Job Number}} & {tex(metadata.job_number)} \\[6pt]
\hline
\textbf{{Date}} & {tex(metadata.report_date)} \\[6pt]
\hline
\textbf{{Report Version}} & {tex(metadata.subtitle or 'Rev 0')} \\[6pt]
\hline
\end{{tabular}}
\end{{table}}
\end{{titlepage}}
\newpage
"""


def toc_section() -> str:
    """Generate Table of Contents."""
    return r"""
\thispagestyle{plain}
\tableofcontents
\newpage
"""

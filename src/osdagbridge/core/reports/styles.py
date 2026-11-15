"""Centralized visual style settings for OsdagBridge LaTeX reports.

Keep page geometry, table spacing, and brand color here so report chapters use
one consistent presentation. These settings affect layout only, not engineering
calculations or design-check results.
"""

GEOMETRY_PACKAGE = (
    r"\usepackage[a4paper, top=2.5cm, bottom=3.0cm, left=2.1cm, right=2.1cm, "
    r"headheight=18pt, headsep=9pt, footskip=32pt]{geometry}"
)

TABLE_STYLE_LATEX = r"""
\setlength{\tabcolsep}{4.5pt}
\renewcommand{\arraystretch}{1.10}
\setlength{\LTpre}{0pt}
\setlength{\LTpost}{6pt}
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.8pt}
"""

BRAND_COLOR_LATEX = r"\definecolor{osdagGreen}{HTML}{91B014}"

# Footer rule deliberately avoids negative vertical skips, which can cause the
# software-default note and footer rule to collide with the page number.
FOOTER_RULE_LATEX = r"""
\renewcommand{\footrule}{%
  \ifbool{hasSDonPage}{%
    \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
    \vspace{3pt}%
  }{}%
  \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{3pt}%
}
"""

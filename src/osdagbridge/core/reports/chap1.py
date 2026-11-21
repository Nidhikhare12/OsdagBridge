from osdagbridge.core.reports.report_utils import _tex


def ch1_project_info(m):
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Design Specification} \\
\hline
\textnormal{Project Name} & """ + _tex(m.project_name) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textnormal{Designer} & """ + _tex(m.designer) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Reviewer} & """ + _tex(m.reviewer) + r""" \\
\hline
\textnormal{Organization} & """ + _tex(m.company) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Client} & """ + _tex(m.client) + r""" \\
\hline
\textnormal{Software Version} & OsdagBridge \\
\hline
\end{tabular}


\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}[leftmargin=1.5em, itemsep=2pt]
\item \textbf{IRC 5:2015} - Standard Specifications and Code of Practice for Road Bridges, Section I: General Features of Design
\item \textbf{IRC 6:2017} - Standard Specifications and Code of Practice for Road Bridges, Section II: Loads and Load Combinations
\item \textbf{IRC 22:2015} - Standard Specifications and Code of Practice for Road Bridges, Section VI: Composite Construction (Limit State Method)
\item \textbf{IRC 24:2010} - Standard Specifications and Code of Practice for Road Bridges, Section V: Steel Road Bridges (Limit State Method)
\item \textbf{IRC 112:2020} - Code of Practice for Concrete Road Bridges (Deck Slab Design)
\item \textbf{IRC SP 114:2018} - Guidelines for Seismic Design of Road Bridges
\item \textbf{IS 800:2007} - General Construction in Steel - Code of Practice
\item \textbf{IS 2062:2011} - Hot Rolled Medium and High Tensile Structural Steel - Specification
\end{itemize}

\vspace{0.8em}
\section{Nomenclature and Acronyms}
\label{sec:nomenclature}

\begingroup
\small
\begin{longtable}{|C{2.6cm}|L{11.4cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Term / Acronym} & \textbf{Engineering Definition} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Nomenclature and Acronyms (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Term / Acronym} & \textbf{Engineering Definition} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
SW & Self-Weight (Dead load of structural members) \\[4pt]
\hline
\rowcolor{OsdagZebra}
DW & Dead Load of Surfacing and Superimposed Dead Load (Wearing Course) \\[4pt]
\hline
SIDL & Superimposed Dead Load (Crash barriers, railings, utilities) \\[4pt]
\hline
\rowcolor{OsdagZebra}
LL & Vehicular Live Load (IRC Class A, 70R, Special Vehicles) \\[4pt]
\hline
WL & Wind Load evaluated per IRC 6:2017 Clause 209 \\[4pt]
\hline
\rowcolor{OsdagZebra}
EL / EQ & Earthquake / Seismic Load evaluated per IRC 6 and IRC SP 114 \\[4pt]
\hline
TL & Temperature Load (Thermal range, rise, and fall) per IRC 6 \\[4pt]
\hline
\rowcolor{OsdagZebra}
ITS & Intermediate Transverse Stiffeners \\[4pt]
\hline
LTB & Lateral Torsional Buckling of steel flexural members \\[4pt]
\hline
\rowcolor{OsdagZebra}
ULS & Ultimate Limit State (Strength, stability, and equilibrium) \\[4pt]
\hline
SLS & Serviceability Limit State (Deflection, crack width, stress limits, fatigue) \\[4pt]
\hline
\rowcolor{OsdagZebra}
UR / DCR & Utilization Ratio / Demand-to-Capacity Ratio (Demand / Capacity $\le$ 1.0) \\[4pt]
\hline
BoQ & Bill of Quantities / Material Take-off \\[4pt]
\hline
\rowcolor{OsdagZebra}
c/c & Centre-to-Centre dimension spacing \\[4pt]
\hline
\end{longtable}
\endgroup
"""



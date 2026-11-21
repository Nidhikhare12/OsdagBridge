from osdagbridge.core.reports.report_utils import _tex


def ch1_project_info(m):
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Project Name} & """ + _tex(m.project_name) + r""" \\
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Designer} & """ + _tex(m.designer) + r""" \\
\hline
\textbf{Reviewer} & """ + (_tex(m.reviewer) if m.reviewer and str(m.reviewer).strip() else 'Not specified') + r""" \\
\hline
\textbf{Organization} & """ + _tex(m.company) + r""" \\
\hline
\textbf{Client} & """ + _tex(m.client) + r""" \\
\hline
\textbf{Job Number} & """ + (_tex(m.job_number) if m.job_number and str(m.job_number).strip() else 'Not specified') + r""" \\
\hline
\textbf{Software Version} & OsdagBridge \\
\hline
\end{tabular}


\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
\item Indian Roads Congress (IRC) 5:2015: General Features of Design
\item Indian Roads Congress (IRC) 6:2017: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22:2015: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24:2010: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112:2020: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114:2018: Seismic Design of Road Bridges
\item Indian Standard (IS) 800:2007: General Construction in Steel
\item Indian Standard (IS) 456:2000: Plain and Reinforced Concrete
\item Indian Standard (IS) 1786:2008: High Strength Deformed Steel Bars and Wires for Concrete Reinforcement
\item Indian Standard (IS) 1893 (Part 3):2014: Criteria for Earthquake Resistant Design of Structures --- Bridges and Retaining Walls
\item Indian Standard (IS) 2062:2011: Hot Rolled Medium and High Tensile Structural Steel
\end{itemize}
"""



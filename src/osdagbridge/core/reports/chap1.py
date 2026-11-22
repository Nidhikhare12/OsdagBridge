from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.reports.styles import COL_PARAM_VALUE, VSPACE_SECTION, lt_begin, lt_end


def ch1_project_info(m):
    table = (
        lt_begin(
            COL_PARAM_VALUE,
            "Project and Design Team Details",
            r"\textbf{Field} & \textbf{Value} \\",
        )
        + r"\textbf{Project Name} & " + _tex(m.project_name) + r" \\" + "\n\\hline\n"
        + r"\textbf{Project Location} & " + _tex(m.project_location) + r" \\" + "\n\\hline\n"
        + r"\textbf{Designer} & " + _tex(m.designer) + r" \\" + "\n\\hline\n"
        + r"\textbf{Reviewer} & " + _tex(m.reviewer) + r" \\" + "\n\\hline\n"
        + r"\textbf{Organization} & " + _tex(m.company) + r" \\" + "\n\\hline\n"
        + r"\textbf{Client} & " + _tex(m.client) + r" \\" + "\n\\hline\n"
        + r"\textbf{Software Version} & OsdagBridge \\" + "\n"
        + lt_end()
    )
    return (
        r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

"""
        + VSPACE_SECTION + "\n"
        + table
        + r"""

\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
\item Indian Roads Congress (IRC) 5: General Features of Design
\item Indian Roads Congress (IRC) 6: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges
\item Indian Standard (IS) 800: General Construction in Steel
\item Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification
\item Indian Standard (IS) 6006: Steel Bearings
\end{itemize}
"""
    )
